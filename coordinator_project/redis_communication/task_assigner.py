"""
Assignation des tâches par le Coordinateur (file d'attente → volontaires).

Le Manager soumet et crée les tâches ; le Coordinateur décide qui exécute quoi.
"""

from __future__ import annotations

import logging
import time
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import redis
from django.conf import settings

from manager.models import Task, TaskAssignment, Workflow
from redis_communication.client import RedisClient
from redis_communication.utils import get_available_volunteers, get_coordinator_token
from redis_communication.volunteer_matching import (
    ACTIVE_ASSIGNMENT_STATUSES,
    volunteer_active_task_count,
    task_estimated_seconds,
    volunteer_can_run_task,
    volunteer_is_assignable,
    volunteer_remaining_capacity_seconds,
)
from volunteer.models import Volunteer

logger = logging.getLogger(__name__)

PENDING_STATUSES = ("PENDING", "CREATED")
_LAST_ASSIGNED_KEY = "coord:assign:last_ts"
_ASSIGN_LOCK_KEY = "coord:assign:lock"
_ASSIGN_LOCK_TTL = 25


def _redis_raw():
    try:
        return RedisClient.get_instance().redis
    except Exception:
        return None


def _last_assigned_score(vid: str) -> float:
    """Horodatage de dernière assignation (plus petit = prioritaire)."""
    client = _redis_raw()
    if not client:
        return 0.0
    try:
        raw = client.hget(_LAST_ASSIGNED_KEY, str(vid))
        if raw is None:
            return 0.0
        if isinstance(raw, bytes):
            raw = raw.decode()
        return float(raw)
    except Exception:
        return 0.0


def _mark_assigned(vid: str) -> None:
    client = _redis_raw()
    if not client:
        return
    try:
        client.hset(_LAST_ASSIGNED_KEY, str(vid), str(time.time()))
    except Exception:
        pass


def _try_assignment_lock() -> bool:
    """Évite les cycles concurrents (N partitions → N threads)."""
    client = _redis_raw()
    if not client:
        return True
    try:
        # SET NX EX
        return bool(client.set(_ASSIGN_LOCK_KEY, "1", nx=True, ex=_ASSIGN_LOCK_TTL))
    except Exception:
        return True


def _release_assignment_lock() -> None:
    client = _redis_raw()
    if not client:
        return
    try:
        client.delete(_ASSIGN_LOCK_KEY)
    except Exception:
        pass


def _release_surplus_assignments_for_volunteer(volunteer) -> int:
    """
    Garde au plus 1 assignation active par volontaire.
    Les tâches en trop repassent en PENDING pour les autres volontaires.
    """
    from manager.models import TaskAssignment

    links = list(
        TaskAssignment.objects.filter(
            volunteer=volunteer,
            status__in=ACTIVE_ASSIGNMENT_STATUSES,
        ).order_by("-status", "assigned_at")  # STARTED before ASSIGNED roughly; then oldest
    )
    # Prefer keeping a STARTED/RESUMED task; otherwise the oldest ASSIGNED.
    keep = None
    for link in links:
        st = str(link.status or "").upper()
        if st in ("STARTED", "RESUMED"):
            keep = link
            break
    if keep is None and links:
        keep = min(
            links,
            key=lambda a: a.assigned_at or datetime.min.replace(tzinfo=timezone.utc),
        )

    released = 0
    for link in links:
        if keep is not None and str(link.id) == str(keep.id):
            continue
        task = link.task
        link.status = "CANCELLED"
        link.save()
        if task and str(task.status or "").upper() in ("ASSIGNED", "PENDING", "CREATED"):
            task.status = "PENDING"
            task.assigned_to = None
            task.progress = 0
            task.save()
            released += 1
            logger.info(
                "Surplus libéré: tâche %s du volontaire %s → PENDING",
                task.id,
                volunteer.id,
            )
    return released


def _cleanup_stale_active_assignments() -> int:
    """
    Annule les assignations actives incohérentes :
    - volontaire manquant
    - tâche manquante / terminale / progress≈100% restée ASSIGNED
    Sans ça, un STARTED fantôme bloque à jamais « 1 tâche par volontaire ».
    """
    from redis_communication.volunteer_matching import _task_is_effectively_done

    released = 0
    for link in list(TaskAssignment.objects.filter(status__in=ACTIVE_ASSIGNMENT_STATUSES)):
        task = link.task
        vol = link.volunteer
        reason = None
        if not vol:
            reason = "volontaire manquant"
        elif not task:
            reason = "tâche manquante"
        elif _task_is_effectively_done(task):
            st = str(getattr(task, "status", "") or "")
            prog = getattr(task, "progress", None)
            reason = f"tâche déjà terminée (status={st}, progress={prog})"
            # Guérir le statut tâche si progress=100 mais status encore ASSIGNED
            if str(st).upper() not in ("COMPLETED", "FAILED", "CANCELLED", "TIMEOUT"):
                try:
                    task.status = "COMPLETED"
                    task.progress = 100
                    if not getattr(task, "end_time", None):
                        task.end_time = datetime.now(timezone.utc)
                    task.save()
                except Exception as exc:
                    logger.debug("heal task status: %s", exc)
            try:
                link.status = "COMPLETED"
                link.progress = 100
                link.completed_at = datetime.now(timezone.utc)
                link.save()
            except Exception:
                link.status = "CANCELLED"
                link.save()
            released += 1
            logger.info(
                "Assignation stale fermée (%s): assignment=%s task=%s",
                reason,
                link.id,
                getattr(task, "id", None),
            )
            continue
        if not reason:
            continue
        link.status = "CANCELLED"
        link.save()
        released += 1
        logger.info(
            "Assignation stale annulée (%s): assignment=%s task=%s",
            reason,
            link.id,
            getattr(task, "id", None),
        )
    return released


def _enforce_one_active_assignment_per_volunteer() -> int:
    """Démêle les piles historiques (N tâches ASSIGNED au même volontaire)."""
    released = _cleanup_stale_active_assignments()
    seen = set()
    for link in TaskAssignment.objects.filter(status__in=ACTIVE_ASSIGNMENT_STATUSES):
        vol = link.volunteer
        if not vol:
            continue
        vid = str(vol.id)
        if vid in seen:
            continue
        seen.add(vid)
        if volunteer_active_task_count(vol) > 1:
            released += _release_surplus_assignments_for_volunteer(vol)
    return released


def _public_coordinator_host() -> str:
    """Adresse joignable par les volontaires externes (pas l'IP Docker interne)."""
    import os

    host = (
        os.environ.get("COORDINATOR_PUBLIC_IP")
        or getattr(settings, "COORDINATOR_PUBLIC_IP", None)
        or os.environ.get("COORDINATOR_PUBLIC_HOST")
        or getattr(settings, "COORDINATOR_PUBLIC_HOST", None)
    )
    if host:
        return str(host)
    # Dériver depuis l'URL publique si configurée
    url = getattr(settings, "COORDINATOR_PUBLIC_URL", "") or os.environ.get(
        "COORDINATOR_PUBLIC_URL", ""
    )
    if url:
        from urllib.parse import urlparse

        parsed = urlparse(url if "://" in url else f"https://{url}")
        if parsed.hostname:
            return parsed.hostname
    return "173.249.38.251"


def _rewrite_input_data_for_volunteer(
    input_data: Dict[str, Any], workflow_id: str
) -> Dict[str, Any]:
    """Pointe les volontaires vers l'API publique du manager (HTTPS).

    Important: conserver l'UUID manager déjà présent dans base_url.
    Remplacer par l'id Mongo du coordinateur provoque des 404
    (No Workflow matches the given query).
    """
    if not input_data:
        return input_data or {}
    data = dict(input_data)

    import os
    import re
    from urllib.parse import urlparse

    manager_url = (
        os.environ.get("MANAGER_PUBLIC_URL")
        or getattr(settings, "MANAGER_PUBLIC_URL", None)
        or "https://manager-vc-uy.npe-techs.com"
    ).rstrip("/")
    if "://" not in manager_url:
        manager_url = f"https://{manager_url}"
    parsed = urlparse(manager_url)
    host = parsed.hostname or "manager-vc-uy.npe-techs.com"
    scheme = parsed.scheme or "https"
    port = 443 if scheme == "https" else 80

    existing = dict(data.get("file_server") or {})
    existing_base = (existing.get("base_url") or "").strip()

    # Extraire l'UUID manager depuis l'URL d'origine si présente
    manager_wf_id = ""
    m = re.search(r"/api/workflow-files/([0-9a-fA-F-]{36})", existing_base)
    if m:
        manager_wf_id = m.group(1)
    if not manager_wf_id:
        manager_wf_id = str(workflow_id or "").strip()

    if not manager_wf_id:
        return data

    base = f"{scheme}://{parsed.netloc}/api/workflow-files/{manager_wf_id}"
    data["file_server"] = {
        "host": host,
        "port": port,
        "base_url": base,
        "path": "",
        "mode": "public_api",
        # Conserver l'UUID manager pour les republications
        "manager_workflow_id": manager_wf_id,
    }
    if existing.get("result_upload_url"):
        data["result_upload_url"] = existing["result_upload_url"]
    return data


def _volunteer_proxy_redis() -> redis.Redis:
    """Redis vu par les volontaires externes (même instance que le gateway 6380)."""
    import os

    # Préférer le Redis interne (socat gateway → redis:6379). Évite NOAUTH du proxy Python.
    host = (
        getattr(settings, "VOLUNTEER_REDIS_HOST", None)
        or os.environ.get("VOLUNTEER_REDIS_HOST")
        or getattr(settings, "REDIS_HOST", None)
        or os.environ.get("REDIS_HOST")
        or "redis"
    )
    port = int(
        getattr(settings, "VOLUNTEER_REDIS_PORT", None)
        or os.environ.get("VOLUNTEER_REDIS_PORT")
        or getattr(settings, "REDIS_PORT", None)
        or os.environ.get("REDIS_PORT")
        or 6379
    )
    return redis.Redis(host=host, port=port, db=0, decode_responses=True)


def _publish_assignment_message(payload: Dict[str, Any]) -> None:
    """Publie task/assignment sur le bus interne + proxy volontaires."""
    import json

    token = get_coordinator_token()
    message = {
        "request_id": str(uuid.uuid4()),
        "sender": {"type": "coordinator", "id": "coordinator"},
        "message_type": "request",
        "timestamp": datetime.now(timezone.utc).timestamp(),
        "token": token,
        "data": payload,
    }
    raw = json.dumps(message)

    client = RedisClient.get_instance()
    client.publish("task/assignment", payload, token=token, real_sender_id="coordinator")

    try:
        proxy = _volunteer_proxy_redis()
        proxy.publish("task/assignment", raw)
        proxy.close()
    except Exception as exc:
        logger.warning("Publication proxy volontaires échouée: %s", exc)


def _notify_manager_assigned(task: Task, volunteer_id: str) -> None:
    """Informe le Manager qu'une tâche a été assignée par le Coordinateur."""
    wf = task.workflow
    meta = task.metadata or {}
    payload = {
        "task_id": str(task.id),
        "workflow_id": str(wf.id) if wf else None,
        "volunteer_id": volunteer_id,
        "status": "ASSIGNED",
        "progress": float(task.progress or 0),
        "name": task.name,
        "message": "Assignée par le coordinateur",
        "input_data": task.input_data or {},
        "estimated_execution_time": task.estimated_execution_time,
        "docker_information": task.docker_information or {},
        "workflow_type": getattr(wf, "workflow_type", "") if wf else "",
        "manager_id": str(getattr(wf, "owner", None).id) if wf and getattr(wf, "owner", None) else None,
    }
    try:
        client = RedisClient.get_instance()
        client.publish(
            "coordinator/task_assigned",
            payload,
            token=get_coordinator_token(),
            real_sender_id="coordinator",
        )
    except Exception as exc:
        logger.warning("Notification manager task_assigned échouée: %s", exc)


def _pending_tasks_global() -> List[Task]:
    """Tâches en file, triées par priorité workflow puis FIFO."""
    workflows = Workflow.objects.filter(
        status__in=["PENDING", "RUNNING", "ASSIGNING", "CREATED", "SUBMITTED"]
    ).order_by("-priority", "submitted_at", "created_at")

    tasks: List[Task] = []
    for wf in workflows:
        for task in Task.objects.filter(workflow=wf, status__in=PENDING_STATUSES).order_by(
            "created_at"
        ):
            task.workflow = wf
            # Pas déjà assignée activement
            active = TaskAssignment.objects.filter(
                task=task,
                status__in=("ASSIGNED", "STARTED", "RESUMED"),
            ).count()
            if active:
                continue
            tasks.append(task)
    return tasks


def _build_assignment_payload(task: Task, volunteer_id: str) -> Dict[str, Any]:
    wf = task.workflow
    meta = task.metadata or {}
    input_data = task.input_data or meta.get("input_data") or {}
    coord_wf_id = str(wf.id) if wf else ""
    input_data = _rewrite_input_data_for_volunteer(input_data, coord_wf_id)
    # Préférer l'UUID manager (celui des fichiers) pour le payload volontaire
    manager_wf_id = (
        (input_data.get("file_server") or {}).get("manager_workflow_id")
        or coord_wf_id
    )
    return {
        "task_id": str(task.id),
        "name": task.name,
        "description": task.description or "",
        "command": task.command or "",
        "dependencies": task.dependencies or [],
        "is_subtask": bool(task.is_subtask),
        "status": "ASSIGNED",
        "required_resources": task.required_resources or {},
        "attempts": task.attempts or (getattr(wf, "attempts", 3) if wf else 3),
        "workflow_id": manager_wf_id,
        "workflow_name": wf.name if wf else "",
        "workflow_description": (wf.description or "") if wf else "",
        "workflow_type": getattr(wf, "workflow_type", "") if wf else "",
        "parameters": task.parameters or [],
        "estimated_execution_time": task_estimated_seconds(task),
        "input_data": input_data,
        "input_data_size": task.input_data_size or meta.get("input_data_size") or 0,
        "docker_information": task.docker_information or meta.get("docker_information") or {},
    }


def assign_pending_tasks(limit: int = 50) -> Dict[str, Any]:
    """
    Point d'entrée : assigne depuis la file globale selon capacité volontaires.
    Une seule tâche active par volontaire, répartition round-robin / moins chargé.
    """
    if not _try_assignment_lock():
        return {"assigned": 0, "message": "Cycle d'assignation déjà en cours"}

    try:
        return _assign_pending_tasks_locked(limit=limit)
    finally:
        _release_assignment_lock()


def _assign_pending_tasks_locked(*, limit: int = 200) -> Dict[str, Any]:
    released = _enforce_one_active_assignment_per_volunteer()
    if released:
        logger.info("Pré-nettoyage: %s assignation(s) surplus libérée(s)", released)

    volunteers_data = get_available_volunteers()
    if not volunteers_data:
        return {"assigned": 0, "message": "Aucun volontaire disponible (hors plage ou offline)"}

    # Charger objets Volunteer + budget temps
    volunteer_objs: List[Tuple[str, Volunteer]] = []
    remaining: Dict[str, Optional[float]] = {}
    for vdata in volunteers_data:
        vid = str(vdata.get("volunteer_id") or "")
        if not vid:
            continue
        vol = Volunteer.objects(id=vid).first()
        if not vol:
            continue
        if not volunteer_is_assignable(vol):
            logger.debug("Volontaire %s ignoré (busy/hors plage)", vid)
            continue
        # Stratégie "1 tâche à la fois" : ne pas empiler plusieurs tâches actives.
        active_tasks = volunteer_active_task_count(vol)
        if active_tasks > 0:
            logger.info(
                "Volontaire %s ignoré (déjà %s tâche(s) active(s))",
                vid,
                active_tasks,
            )
            continue
        volunteer_objs.append((vid, vol))
        remaining[vid] = volunteer_remaining_capacity_seconds(vol)

    if not volunteer_objs:
        if volunteers_data:
            return {
                "assigned": 0,
                "message": "Volontaire(s) en ligne mais déjà occupé(s) ou hors critères d'assignation",
            }
        return {
            "assigned": 0,
            "message": "Aucun volontaire disponible (hors plage ou offline)",
        }

    queue = _pending_tasks_global()
    if not queue:
        return {"assigned": 0, "message": "File d'attente vide"}

    by_volunteer: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    assigned_count = 0
    assigned_this_cycle: set[str] = set()

    for task in queue:
        if assigned_count >= limit:
            break
        eligible: List[Tuple[str, Volunteer]] = []
        for vid, vol in volunteer_objs:
            if vid in assigned_this_cycle:
                continue
            budget = remaining[vid]
            if volunteer_can_run_task(vol, task, remaining_seconds=budget):
                eligible.append((vid, vol))
        if not eligible:
            continue

        def _sort_key(item: Tuple[str, Volunteer]):
            vid, _ = item
            # Priorité: qui n'a pas eu de travail récemment (round-robin LRU)
            last_ts = _last_assigned_score(vid)
            budget = remaining[vid]
            # budget None (illimité) = OK; budget fini = encore disponible
            budget_rank = 0 if budget is None else (0 if float(budget) > 0 else 1)
            return (budget_rank, last_ts, vid)

        eligible.sort(key=_sort_key)

        chosen = None
        for volunteer_id, volunteer in eligible:
            from redis_communication.availability_probe import probe_volunteer_availability

            probe = probe_volunteer_availability(volunteer_id, horizon_min=15)
            # Soft gate: ne bloque en dur que si STRICT + launch=False explicite non dégradé.
            # Sinon (timeout, bridge dégradé, batterie) on assigne quand même et on
            # journalise — sinon une sonde fail/ORPHAN bloque toute la file.
            import os as _os

            strict = str(
                _os.environ.get("COORDINATOR_AVAILABILITY_STRICT", "0")
            ).lower() in ("1", "true", "yes", "on")
            hard_block = (
                strict
                and probe.get("ok")
                and probe.get("launch") is False
                and not probe.get("degraded")
            )
            if hard_block:
                logger.info(
                    "Volontaire %s écarté (STRICT) prédicteur 15min (launch=%s hybrid=%s)",
                    volunteer_id,
                    probe.get("launch"),
                    probe.get("hybrid"),
                )
                continue
            if probe.get("launch") is False or probe.get("degraded"):
                logger.info(
                    "Prédicteur soft pour %s (launch=%s degraded=%s src=%s) — assignation quand même",
                    volunteer_id,
                    probe.get("launch"),
                    probe.get("degraded"),
                    probe.get("source"),
                )
            chosen = (volunteer_id, volunteer, probe)
            break

        if not chosen:
            continue

        volunteer_id, volunteer, probe = chosen
        est = task_estimated_seconds(task)

        TaskAssignment.objects(
            task=task, status__in=ACTIVE_ASSIGNMENT_STATUSES
        ).update(status="CANCELLED")
        TaskAssignment(
            task=task,
            volunteer=volunteer,
            status="ASSIGNED",
            assigned_at=datetime.now(timezone.utc),
            progress=0,
        ).save()

        task.assigned_to = volunteer
        task.status = "ASSIGNED"
        # Trace prédiction (audit recherche)
        meta = dict(task.metadata or {})
        meta["availability_probe"] = {
            "hybrid": probe.get("hybrid"),
            "gru": probe.get("gru"),
            "linear": probe.get("linear"),
            "horizon_min": probe.get("horizon_min", 15),
            "launch": True,
        }
        task.metadata = meta
        task.save()

        wf = task.workflow
        if wf and wf.status in ("CREATED", "PENDING", None, ""):
            wf.status = "RUNNING"
            wf.save()

        entry = _build_assignment_payload(task, volunteer_id)
        by_volunteer[volunteer_id].append(entry)

        if remaining[volunteer_id] is not None:
            remaining[volunteer_id] = max(0.0, float(remaining[volunteer_id]) - est)

        _notify_manager_assigned(task, volunteer_id)
        _mark_assigned(volunteer_id)
        assigned_count += 1
        assigned_this_cycle.add(volunteer_id)
        logger.info(
            "Fair-share: tâche %s → volontaire %s (last_ts rotated)",
            getattr(task, "name", task.id),
            volunteer_id[:8],
        )

    published = 0
    for volunteer_id, task_list in by_volunteer.items():
        if not task_list:
            continue
        wf_id = task_list[0].get("workflow_id") or ""
        wf = None
        if wf_id:
            from manager.models import Workflow as CoordWorkflow
            try:
                wf = CoordWorkflow.objects.get(id=wf_id)
            except Exception:
                wf = None
        _publish_assignment_message(
            {
                "workflow_id": wf_id,
                "workflow_name": (wf.name if wf else task_list[0].get("workflow_name")) or "",
                "workflow_description": (wf.description if wf else task_list[0].get("workflow_description")) or "",
                "workflow_type": (getattr(wf, "workflow_type", "") if wf else task_list[0].get("workflow_type")) or "",
                "assignments": {volunteer_id: task_list},
            }
        )
        published += len(task_list)
        logger.info(
            "Coordinateur: %s tâche(s) → volontaire %s",
            len(task_list),
            volunteer_id,
        )

    msg = (
        f"{published} tâche(s) assignée(s) par le coordinateur"
        if published
        else "Aucune assignation (capacité/préférences insuffisantes)"
    )
    return {"assigned": published, "message": msg}


def republish_assigned_tasks(limit: int = 50) -> Dict[str, Any]:
    """
    Renvoie au volontaire les tâches déjà ASSIGNED mais jamais démarrées (0%).
    Utile quand le volontaire était hors ligne au moment de la première assignation.
    """
    volunteers_data = get_available_volunteers()
    if not volunteers_data:
        return {"republished": 0, "message": "Aucun volontaire en ligne"}

    online_ids = {
        str(v.get("volunteer_id"))
        for v in volunteers_data
        if v.get("volunteer_id")
    }

    by_volunteer: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    republished = 0
    already_has_task: set[str] = set()

    for assignment in TaskAssignment.objects(status="ASSIGNED").order_by("assigned_at"):
        if republished >= limit:
            break
        task = assignment.task
        if not task or float(task.progress or 0) > 0:
            continue
        if str(task.status or "").upper() not in ("ASSIGNED", "PENDING", "CREATED"):
            continue
        vol = assignment.volunteer
        if not vol:
            continue
        vid = str(vol.id)
        if vid not in online_ids or not volunteer_is_assignable(vol):
            continue
        # Une seule tâche republiée par volontaire (fair-share).
        if vid in already_has_task or by_volunteer[vid]:
            continue
        if volunteer_active_task_count(vol) > 1:
            _release_surplus_assignments_for_volunteer(vol)
            # Re-check: only republish if this assignment is still the kept one.
            assignment.reload()
            if str(assignment.status or "").upper() != "ASSIGNED":
                continue
        by_volunteer[vid].append(_build_assignment_payload(task, vid))
        already_has_task.add(vid)
        republished += 1

    published = 0
    for volunteer_id, task_list in by_volunteer.items():
        if not task_list:
            continue
        wf_id = task_list[0].get("workflow_id") or ""
        wf = None
        if wf_id:
            from manager.models import Workflow as CoordWorkflow
            try:
                wf = CoordWorkflow.objects.get(id=wf_id)
            except Exception:
                wf = None
        _publish_assignment_message(
            {
                "workflow_id": wf_id,
                "workflow_name": (wf.name if wf else task_list[0].get("workflow_name")) or "",
                "workflow_description": (wf.description if wf else task_list[0].get("workflow_description")) or "",
                "workflow_type": (getattr(wf, "workflow_type", "") if wf else task_list[0].get("workflow_type")) or "",
                "assignments": {volunteer_id: task_list},
            }
        )
        published += len(task_list)
        logger.info(
            "Republication coordinateur: %s tâche(s) → volontaire %s",
            len(task_list),
            volunteer_id,
        )

    msg = (
        f"{published} tâche(s) republiée(s) vers volontaires en ligne"
        if published
        else "Aucune tâche ASSIGNED à republier"
    )
    return {"republished": published, "message": msg}


def run_coordinator_assignment_cycle(limit: int = 50) -> Dict[str, Any]:
    """Assigne la file d'attente puis republie les ASSIGNED non démarrées."""
    pending = assign_pending_tasks(limit=limit)
    republish = republish_assigned_tasks(limit=limit)
    return {
        "assigned": pending.get("assigned", 0),
        "republished": republish.get("republished", 0),
        "message": f"{pending.get('message', '')} | {republish.get('message', '')}",
    }
