"""
Présence réelle des volontaires côté Coordinateur.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

ONLINE_TTL_SECONDS = 90


def mark_online(volunteer_id, status: str = "available") -> None:
    from volunteer.models import Volunteer

    if not volunteer_id:
        return
    volunteer = Volunteer.objects(id=volunteer_id).first()
    if not volunteer:
        return
    volunteer.last_activity = datetime.now(timezone.utc)
    if status in ("available", "busy"):
        volunteer.current_status = status
    elif volunteer.current_status == "offline":
        volunteer.current_status = "available"
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
            # Jamais de heartbeat depuis le login: utiliser last_update
            last = volunteer.last_update
        if last is None:
            continue
        # Normaliser timezone-aware
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        if last < cutoff:
            volunteer.current_status = "offline"
            volunteer.save()
            count += 1
            logger.info("Volontaire marqué offline (dernier signal %s): %s", last, volunteer.id)
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
