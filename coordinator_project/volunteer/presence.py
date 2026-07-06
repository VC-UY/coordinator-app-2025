"""
Présence réelle des volontaires côté Coordinateur.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

ONLINE_TTL_SECONDS = 180


def mark_online(
    volunteer_id,
    status: str = "available",
    *,
    preferences: Optional[Dict[str, Any]] = None,
    resources: Optional[Dict[str, Any]] = None,
) -> None:
    from volunteer.models import Volunteer

    if not volunteer_id:
        return

    if status == "offline":
        mark_offline(volunteer_id, reason="schedule")
        return

    volunteer = Volunteer.objects(id=volunteer_id).first()
    if not volunteer:
        return

    volunteer.last_activity = datetime.now(timezone.utc)
    if status in ("available", "busy"):
        volunteer.current_status = status

    if preferences:
        merged = dict(volunteer.preferences or {})
        merged.update(preferences)
        volunteer.preferences = merged
        if preferences.get("max_cpu_cores"):
            volunteer.cpu_cores = int(preferences["max_cpu_cores"])
        if preferences.get("max_ram_gb"):
            volunteer.total_ram = int(float(preferences["max_ram_gb"]) * 1024)
        if preferences.get("max_disk_gb"):
            volunteer.available_storage = int(preferences["max_disk_gb"])

    if resources:
        if resources.get("cpu_cores") is not None:
            volunteer.cpu_cores = int(resources["cpu_cores"])
        if resources.get("memory_mb") is not None:
            volunteer.total_ram = int(resources["memory_mb"])
        if resources.get("disk_space_mb") is not None:
            volunteer.available_storage = max(
                1, int(resources["disk_space_mb"]) // 1024
            )
        if "gpu" in resources:
            volunteer.gpu_available = bool(resources["gpu"])

    volunteer.save()


def mark_offline(volunteer_id, reason: str = "timeout") -> None:
    from volunteer.models import Volunteer

    if not volunteer_id:
        return
    volunteer = Volunteer.objects(id=volunteer_id).first()
    if not volunteer or volunteer.current_status == "offline":
        return
    volunteer.current_status = "offline"
    volunteer.save()
    logger.info("Volontaire offline (%s): %s", reason, volunteer_id)


def sweep_stale_volunteers(ttl_seconds: int = ONLINE_TTL_SECONDS) -> int:
    from volunteer.models import Volunteer

    cutoff = datetime.now(timezone.utc) - timedelta(seconds=ttl_seconds)
    count = 0
    for volunteer in Volunteer.objects(current_status__in=["available", "busy"]):
        last = volunteer.last_activity
        if last is None:
            last = volunteer.last_update
        if last is None:
            continue
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        if last < cutoff:
            volunteer.current_status = "offline"
            volunteer.save()
            count += 1
            logger.info(
                "Volontaire marqué offline (dernier signal %s): %s",
                last,
                volunteer.id,
            )
    return count


def is_online(volunteer) -> bool:
    if not volunteer or volunteer.current_status == "offline":
        return False
    last = volunteer.last_activity or volunteer.last_update
    if not last:
        return False
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    return last >= datetime.now(timezone.utc) - timedelta(seconds=ONLINE_TTL_SECONDS)
