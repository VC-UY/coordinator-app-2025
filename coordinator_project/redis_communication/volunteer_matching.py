"""Filtrage volontaires / capacité pour l'assignation côté Coordinateur."""

from __future__ import annotations

from datetime import datetime, time
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from django.conf import settings

ACTIVE_ASSIGNMENT_STATUSES = ("ASSIGNED", "STARTED", "RESUMED")

DAY_INDEX = {
    "lundi": 0,
    "mardi": 1,
    "mercredi": 2,
    "jeudi": 3,
    "vendredi": 4,
    "samedi": 5,
    "dimanche": 6,
}


def _schedule_tz() -> ZoneInfo:
    name = getattr(settings, "VOLUNTEER_SCHEDULE_TZ", "Europe/Paris")
    try:
        return ZoneInfo(name)
    except Exception:
        return ZoneInfo("Europe/Paris")


def _prefs(volunteer) -> dict:
    return getattr(volunteer, "preferences", None) or {}


def is_within_schedule(prefs: dict, when: Optional[datetime] = None) -> bool:
    """
    True si l'instant `when` tombe dans une plage horaire configurée.
    Même logique que l'app Volontaire (schedule: [{day, start, end}]).
    """
    schedule = prefs.get("schedule") or []
    if not schedule:
        return True

    when = when or datetime.now(_schedule_tz())
    if when.tzinfo is None:
        when = when.replace(tzinfo=_schedule_tz())
    else:
        when = when.astimezone(_schedule_tz())

    today = when.weekday()
    now_t = when.time().replace(second=0, microsecond=0)

    for slot in schedule:
        day = (slot.get("day") or "").strip().lower()
        if DAY_INDEX.get(day) != today:
            continue
        try:
            start = time.fromisoformat(slot.get("start", "00:00"))
            end = time.fromisoformat(slot.get("end", "23:59"))
        except ValueError:
            continue
        if start <= now_t <= end:
            return True
    return False


def volunteer_is_assignable(volunteer, *, when: Optional[datetime] = None) -> bool:
    """Volontaire en ligne, disponible (pas busy) et dans sa plage horaire."""
    if not volunteer:
        return False
    if getattr(volunteer, "current_status", None) != "available":
        return False
    return is_within_schedule(_prefs(volunteer), when=when)


def volunteer_max_capacity_seconds(volunteer) -> Optional[float]:
    prefs = _prefs(volunteer)
    max_min = int(prefs.get("duree_max_execution") or 0)
    if max_min <= 0:
        return None
    return float(max_min) * 60.0


def volunteer_used_capacity_seconds(volunteer) -> float:
    from manager.models import TaskAssignment, Task

    total = 0.0
    for link in TaskAssignment.objects.filter(
        volunteer=volunteer,
        status__in=ACTIVE_ASSIGNMENT_STATUSES,
    ):
        task = link.task
        if not task:
            continue
        if task.status in ("COMPLETED", "FAILED", "CANCELLED"):
            continue
        total += float(getattr(task, "estimated_execution_time", 0) or 0)
    return total


def volunteer_remaining_capacity_seconds(volunteer) -> Optional[float]:
    max_cap = volunteer_max_capacity_seconds(volunteer)
    if max_cap is None:
        return None
    return max(0.0, max_cap - volunteer_used_capacity_seconds(volunteer))


def task_estimated_seconds(task) -> float:
    est = float(getattr(task, "estimated_execution_time", 0) or 0)
    if est <= 0:
        meta = getattr(task, "metadata", None) or {}
        est = float(meta.get("estimated_execution_time") or 0)
    return est if est > 0 else 60.0


def volunteer_can_run_task(
    volunteer,
    task,
    *,
    remaining_seconds: Optional[float] = None,
) -> bool:
    prefs = _prefs(volunteer)

    if not volunteer_is_assignable(volunteer):
        return False
    if not is_within_schedule(prefs):
        return False

    req = task.required_resources or {}
    req_cpu = float(req.get("cpu") or req.get("cpu_cores") or 1)
    req_ram = float(req.get("ram") or req.get("memory_mb") or 512)
    req_disk = float(req.get("disk") or req.get("disk_gb") or 1)

    max_cpu = float(prefs.get("max_cpu_cores") or volunteer.cpu_cores or 1)
    max_ram_mb = float(prefs.get("max_ram_gb") or 0) * 1024.0
    if max_ram_mb <= 0:
        max_ram_mb = float(volunteer.total_ram or 1024)
    max_disk = float(prefs.get("max_disk_gb") or volunteer.available_storage or 1)

    if req_cpu > max_cpu + 0.05:
        return False
    if req_ram > max_ram_mb + 1:
        return False
    if req_disk > max_disk + 0.05:
        return False

    est = task_estimated_seconds(task)
    if remaining_seconds is None:
        remaining_seconds = volunteer_remaining_capacity_seconds(volunteer)
    if remaining_seconds is not None and est > remaining_seconds + 1:
        return False

    types = (prefs.get("types_calcul_autorises") or "").strip()
    if types and task.workflow:
        allowed = {t.strip().upper() for t in types.split(",") if t.strip()}
        wf_type = (getattr(task.workflow, "workflow_type", "") or "").upper()
        if allowed and wf_type and wf_type not in allowed:
            return False

    min_prio = int(prefs.get("priorite_min_acceptee") or 0)
    if task.workflow and min_prio:
        wf_prio = int(getattr(task.workflow, "priority", 0) or 0)
        if wf_prio < min_prio:
            return False

    return True
