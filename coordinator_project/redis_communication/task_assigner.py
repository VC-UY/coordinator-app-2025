"""
Assignation des tâches par le Coordinateur (file d'attente → volontaires).

Le Manager soumet et crée les tâches ; le Coordinateur décide qui exécute quoi.
"""

from __future__ import annotations

import logging
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
    task_estimated_seconds,
    volunteer_can_run_task,
    volunteer_is_assignable,
    volunteer_remaining_capacity_seconds,
)
from volunteer.models import Volunteer

logger = logging.getLogger(__name__)

PENDING_STATUSES = ("PENDING", "CREATED")


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
    """Réécrit file_server pour que le volontaire distant puisse télécharger les entrées."""
    if not input_data:
        return input_data or {}
    data = dict(input_data)
    fs = data.get("file_server")
    if not fs or not workflow_id:
        return data
    host = _public_coordinator_host()
    port = int(getattr(settings, "COORDINATOR_FILE_PORT", 8410))
    proxy_task_id = f"input_{workflow_id}"
    data["file_server"] = {
        **fs,
        "host": host,
        "port": port,
        "base_url": f"http://{host}:{port}",
        "path": f"/files/{proxy_task_id}/",
        "_routed_by": "coordinator_file_proxy",
    }
    return data


def _volunteer_proxy_redis() -> redis.Redis:
    """Redis vu par les volontaires externes (proxy 6380)."""
    host = getattr(settings, "VOLUNTEER_REDIS_HOST", "coordinator-proxy")
    port = int(getattr(settings, "VOLUNTEER_REDIS_PORT", 6380))
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
    wf_id = str(wf.id) if wf else ""
    input_data = _rewrite_input_data_for_volunteer(input_data, wf_id)
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
        "workflow_id": str(wf.id) if wf else "",
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
    """
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
        volunteer_objs.append((vid, vol))
        remaining[vid] = volunteer_remaining_capacity_seconds(vol)

    if not volunteer_objs:
        return {
            "assigned": 0,
            "message": "Aucun volontaire dans sa plage horaire de disponibilité",
        }

    queue = _pending_tasks_global()
    if not queue:
        return {"assigned": 0, "message": "File d'attente vide"}

    by_volunteer: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    assigned_count = 0

    for task in queue:
        if assigned_count >= limit:
            break
        eligible: List[Tuple[str, Volunteer]] = []
        for vid, vol in volunteer_objs:
            budget = remaining[vid]
            if volunteer_can_run_task(vol, task, remaining_seconds=budget):
                eligible.append((vid, vol))
        if not eligible:
            continue

        def _sort_key(item: Tuple[str, Volunteer]):
            vid, _ = item
            budget = remaining[vid]
            if budget is None:
                return (1, 0.0)
            return (0, -budget)

        eligible.sort(key=_sort_key)
        volunteer_id, volunteer = eligible[0]
        est = task_estimated_seconds(task)

        TaskAssignment.objects(task=task, status="ASSIGNED").update(status="CANCELLED")
        TaskAssignment(
            task=task,
            volunteer=volunteer,
            status="ASSIGNED",
            assigned_at=datetime.now(timezone.utc),
            progress=0,
        ).save()

        task.assigned_to = volunteer
        task.status = "ASSIGNED"
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
        assigned_count += 1

    published = 0
    for volunteer_id, task_list in by_volunteer.items():
        if not task_list:
            continue
        wf_id = task_list[0].get("workflow_id") or ""
        _publish_assignment_message(
            {
                "workflow_id": wf_id,
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
        if any(e.get("task_id") == str(task.id) for e in by_volunteer[vid]):
            continue
        by_volunteer[vid].append(_build_assignment_payload(task, vid))
        republished += 1

    published = 0
    for volunteer_id, task_list in by_volunteer.items():
        if not task_list:
            continue
        wf_id = task_list[0].get("workflow_id") or ""
        _publish_assignment_message(
            {
                "workflow_id": wf_id,
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
