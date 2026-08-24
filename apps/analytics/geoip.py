"""IP → country resolution via the free ip-api.com batch endpoint.

Deliberately NOT called from the request path (it makes a network round-trip
and ip-api's free tier is rate-limited: HTTP-only, ~15 batch req/min, ≤100 IPs
per batch). The ``resolve_geoip`` management command calls this on distinct,
unresolved IPs; each IP is resolved once and written to every VisitLog row that
shares it. Any failure degrades to "unresolved" — analytics never blocks on it.
"""
import threading

import requests

# Re-exported so existing callers (middleware, tests) keep using geoip.is_public_ip;
# the implementation now lives in apps.common.utils as the single source of truth.
from apps.common.utils import is_public_ip  # noqa: F401

BATCH_URL = "http://ip-api.com/batch"
_FIELDS = "status,country,countryCode,query"
_MAX_BATCH = 100


def resolve_ips(ips, timeout: int = 10) -> dict:
    """Resolve an iterable of IPs to ``{ip: (country, country_code)}``.

    Deduplicates, skips non-public IPs, and queries ip-api in batches of 100.
    Returns whatever was resolved; on a network/parse error for a batch it stops
    early and returns what it has so far (callers simply retry later).
    """
    public = [ip for ip in dict.fromkeys(ips) if ip and is_public_ip(ip)]
    resolved = {}
    for start in range(0, len(public), _MAX_BATCH):
        chunk = public[start:start + _MAX_BATCH]
        payload = [{"query": ip, "fields": _FIELDS} for ip in chunk]
        try:
            response = requests.post(BATCH_URL, json=payload, timeout=timeout)
            response.raise_for_status()
            entries = response.json()
        except Exception:
            break
        for entry in entries:
            if entry.get("status") == "success":
                resolved[entry.get("query")] = (
                    entry.get("country", "") or "",
                    entry.get("countryCode", "") or "",
                )
    return resolved


def _backfill(limit):
    """Resolve pending IPs and write them back; swallows everything."""
    from django.db import connection

    from .models import VisitLog
    try:
        ips = list(
            VisitLog.objects.filter(country="")
            .exclude(ip_address__isnull=True)
            .values_list("ip_address", flat=True)
            .distinct()[:limit]
        )
        for ip, (country, code) in resolve_ips(ips).items():
            if country:
                VisitLog.objects.filter(ip_address=ip).update(
                    country=country, country_code=code
                )
    except Exception:
        pass
    finally:
        connection.close()  # this runs in its own thread -> its own connection


def backfill_pending(limit=100):
    """Kick a one-shot background country backfill if any rows are pending.

    ponytail: the primary path is deploy/resolve-geoip.timer; this is the safety
    net for a box where that timer was never installed, so the Locations panel
    is not permanently empty. Cache-locked to once per 15 minutes and capped at
    one ip-api batch, so it can neither storm the API nor the database. Returns
    True if a worker was started.
    """
    from django.core.cache import cache

    from .models import VisitLog
    try:
        pending = (
            VisitLog.objects.filter(country="")
            .exclude(ip_address__isnull=True)
            .exists()
        )
        if not pending or not cache.add("geoip:backfill", 1, 900):
            return False
        threading.Thread(target=_backfill, args=(limit,), daemon=True).start()
        return True
    except Exception:
        return False
