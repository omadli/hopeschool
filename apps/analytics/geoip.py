"""IP → country resolution via the free ip-api.com batch endpoint.

Deliberately NOT called from the request path (it makes a network round-trip
and ip-api's free tier is rate-limited: HTTP-only, ~15 batch req/min, ≤100 IPs
per batch). The ``resolve_geoip`` management command calls this on distinct,
unresolved IPs; each IP is resolved once and written to every VisitLog row that
shares it. Any failure degrades to "unresolved" — analytics never blocks on it.
"""
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
