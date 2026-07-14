"""
Sonde la disponibilité 15 min d'un volontaire via Redis + agent local.
Fallback : dernière prediction_detail synchronisée sur le site public.
"""
from __future__ import annotations

import json
import logging
import os
import time
import urllib.parse
import urllib.request
import uuid
from typing import Any, Dict, Optional

from django.conf import settings

from redis_communication.client import RedisClient
from redis_communication.utils import get_coordinator_token

logger = logging.getLogger(__name__)

QUERY_CHANNEL = "volunteer/availability/query"
REPLY_CHANNEL = "volunteer/availability/reply"
REPLY_KEY_PREFIX = "availability:reply:"


def _enabled() -> bool:
    raw = getattr(settings, "COORDINATOR_AVAILABILITY_PROBE", None)
    if raw is None:
        raw = os.environ.get("COORDINATOR_AVAILABILITY_PROBE", "1")
    return str(raw).lower() in ("1", "true", "yes", "on")


def _timeout_s() -> float:
    return float(
        getattr(settings, "COORDINATOR_AVAILABILITY_TIMEOUT", None)
        or os.environ.get("COORDINATOR_AVAILABILITY_TIMEOUT", "12")
    )


def _site_telemetry_candidates() -> list:
    """URLs internes Docker puis public, avec Host correct pour ALLOWED_HOSTS."""
    custom = (
        getattr(settings, "VCUY_SITE_TELEMETRY_URL", None)
        or os.environ.get("VCUY_SITE_TELEMETRY_URL")
        or ""
    ).strip().rstrip("/")
    headers_base = {"Accept": "application/json"}
    out = []
    if custom:
        out.append((custom, dict(headers_base)))
    out.extend(
        [
            (
                "http://site-backend:8003/api/telemetry/last-prediction",
                {**headers_base, "Host": "vc-uy.npe-techs.com"},
            ),
            (
                "http://127.0.0.1:8003/api/telemetry/last-prediction",
                {**headers_base, "Host": "localhost"},
            ),
            (
                "https://vc-uy.npe-techs.com/api/telemetry/last-prediction",
                dict(headers_base),
            ),
        ]
    )
    seen = set()
    uniq = []
    for url, hdr in out:
        if url in seen:
            continue
        seen.add(url)
        uniq.append((url, hdr))
    return uniq


def _fallback_from_site(volunteer_id: str) -> Optional[Dict[str, Any]]:
    """Dernière prediction_detail syncée par l'agent/bridge vers le site."""
    data = None
    last_err = None
    for base, headers in _site_telemetry_candidates():
        url = f"{base.rstrip('/')}/?volunteer_id={urllib.parse.quote(volunteer_id)}"
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            break
        except Exception as exc:
            last_err = exc
            continue
    try:
        if not isinstance(data, dict) or not data.get("ok"):
            if last_err:
                logger.info("Fallback site prediction indisponible: %s", last_err)
            return None
        detail = data.get("prediction_detail") or {}
        out = {
            "ok": True,
            "source": "site_telemetry_fallback",
            "degraded": True,
            "volunteer_id": volunteer_id,
            "machine_id": data.get("machine_id"),
            "collected_at": data.get("collected_at"),
            "prediction_detail": detail,
            **{k: v for k, v in detail.items() if k not in ("prediction_detail",)},
        }
        if "launch" not in out and out.get("hybrid") is not None:
            thr = float(out.get("launch_threshold") or out.get("threshold") or 0.32)
            out["launch"] = float(out["hybrid"]) >= thr
        return out
    except Exception as exc:
        logger.info("Fallback site prediction indisponible: %s", exc)
        return None


def probe_volunteer_availability(
    volunteer_id: str,
    *,
    horizon_min: int = 15,
    timeout: Optional[float] = None,
) -> Dict[str, Any]:
    """Demande au volontaire une prédiction hybrid/launch 15 min."""
    if not _enabled():
        return {"ok": True, "launch": True, "skipped": True, "reason": "probe_disabled"}

    vid = str(volunteer_id or "")
    if not vid:
        return {"ok": False, "launch": False, "error": "missing_volunteer_id"}

    request_id = str(uuid.uuid4())
    wait = _timeout_s() if timeout is None else float(timeout)
    client = RedisClient.get_instance()
    key = f"{REPLY_KEY_PREFIX}{request_id}"

    try:
        client.redis.delete(key)
    except Exception:
        pass

    try:
        client.publish(
            QUERY_CHANNEL,
            {
                "volunteer_id": vid,
                "request_id": request_id,
                "horizon_min": horizon_min,
            },
            request_id=request_id,
            token=get_coordinator_token(),
            message_type="request",
            real_sender_id="coordinator",
        )
    except Exception as exc:
        logger.warning("Échec publication sonde disponibilité: %s", exc)
        fb = _fallback_from_site(vid)
        if fb:
            fb["error"] = f"publish_failed:{exc}"
            _store_probe_history(client, fb)
            return fb
        return {
            "ok": False,
            "launch": None,
            "degraded": True,
            "source": "timeout",
            "error": f"publish_failed:{exc}",
            "volunteer_id": vid,
            "prediction_detail": {},
        }

    deadline = time.time() + wait
    while time.time() < deadline:
        try:
            raw = client.redis.get(key)
        except Exception as exc:
            fb = _fallback_from_site(vid)
            if fb:
                fb["error"] = f"redis_get:{exc}"
                fb["request_id"] = request_id
                fb["probed_at"] = time.time()
                _store_probe_history(client, fb)
                return fb
            return {
                "ok": False,
                "launch": None,
                "degraded": True,
                "source": "timeout",
                "error": f"redis_get:{exc}",
                "request_id": request_id,
                "volunteer_id": vid,
                "prediction_detail": {},
            }
        if raw:
            try:
                if isinstance(raw, bytes):
                    raw = raw.decode("utf-8")
                data = json.loads(raw)
                data.setdefault("ok", True)
                data["volunteer_id"] = vid
                data["probed_at"] = time.time()
                data.setdefault("source", "redis_probe")
                detail = data.get("prediction_detail") or {}
                for k, v in detail.items():
                    data.setdefault(k, v)
                _store_probe_history(client, data)
                logger.info(
                    "Sonde disponibilité %s → launch=%s hybrid=%s",
                    vid[:8],
                    data.get("launch"),
                    data.get("hybrid"),
                )
                return data
            except Exception as exc:
                return {
                    "ok": False,
                    "launch": None,
                    "degraded": True,
                    "source": "timeout",
                    "error": f"bad_payload:{exc}",
                    "volunteer_id": vid,
                    "prediction_detail": {},
                }
        time.sleep(0.15)

    logger.info("Sonde disponibilité timeout pour volontaire %s (%.1fs)", vid[:8], wait)

    fb = _fallback_from_site(vid)
    if fb:
        fb["error"] = "redis_timeout_used_site_fallback"
        fb["request_id"] = request_id
        fb["probed_at"] = time.time()
        _store_probe_history(client, fb)
        return fb

    strict = str(
        getattr(settings, "COORDINATOR_AVAILABILITY_STRICT", None)
        or os.environ.get("COORDINATOR_AVAILABILITY_STRICT", "0")
    ).lower() in ("1", "true", "yes", "on")
    result = {
        "ok": not strict,
        "launch": None if not strict else False,
        "launch_assumed": (not strict),
        "degraded": True,
        "error": "timeout",
        "source": "timeout",
        "request_id": request_id,
        "volunteer_id": vid,
        "probed_at": time.time(),
        "prediction_detail": {},
    }
    if strict:
        result["ok"] = False
        result["launch"] = False
        result["launch_assumed"] = False
    _store_probe_history(client, result)
    return result


def _store_probe_history(client, data: Dict[str, Any]) -> None:
    try:
        payload = json.dumps(data, default=str)
        vid = str(data.get("volunteer_id") or "")
        if vid:
            client.redis.hset("availability:last", vid, payload)
        client.redis.lpush("availability:history", payload)
        client.redis.ltrim("availability:history", 0, 199)
    except Exception as exc:
        logger.debug("store probe history: %s", exc)


def list_recent_probes(limit: int = 50) -> list:
    client = RedisClient.get_instance()
    raws = client.redis.lrange("availability:history", 0, max(0, limit - 1))
    out = []
    for raw in raws or []:
        try:
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8")
            out.append(json.loads(raw))
        except Exception:
            continue
    return out


def list_last_probes_by_volunteer() -> dict:
    client = RedisClient.get_instance()
    try:
        raw = client.redis.hgetall("availability:last") or {}
    except Exception:
        return {}
    out = {}
    for k, v in raw.items():
        if isinstance(k, bytes):
            k = k.decode()
        if isinstance(v, bytes):
            v = v.decode()
        try:
            out[str(k)] = json.loads(v)
        except Exception:
            continue
    return out
