import hashlib

import user_agents
from django.conf import settings
from django.utils import timezone

from apps.common.utils import client_ip, is_public_ip

from .models import VisitLog

# Path prefixes that should never be logged as a public page visit. The admin
# prefix is NOT listed here — it is configurable (settings.ADMIN_URL) and is
# derived per request in _log(), otherwise a custom ADMIN_URL (e.g.
# "kirma-bu-yerga/") would be counted as a public visit.
SKIP_PREFIXES = (
    "/static",
    "/media",
    "/favicon",
    "/i18n",
    "/ckeditor5",
)

# Country marker for visitors whose IP is private/loopback (dev machine, LAN,
# health check). "ZZ" is the ISO 3166-1 user-assigned code, so it can never
# collide with a real country, and a non-empty country keeps resolve_geoip from
# pointlessly re-querying these rows.
LOCAL_COUNTRY = "Local"
LOCAL_CODE = "ZZ"


def _device_type(ua):
    if ua.is_mobile:
        return VisitLog.DeviceType.MOBILE
    if ua.is_tablet:
        return VisitLog.DeviceType.TABLET
    if ua.is_pc:
        return VisitLog.DeviceType.DESKTOP
    return VisitLog.DeviceType.OTHER


def visitor_hash(ip, user_agent, day=None):
    """Pseudonymous per-day visitor id — the "users" unit on the dashboard.

    Salted with SECRET_KEY and rotated daily, so the hash can neither be
    reversed to an IP nor used to follow someone across days. A visitor who
    browses across midnight simply counts once per day (same trade-off as
    cookie-less analytics like Plausible).
    """
    day = day or timezone.localdate()
    raw = f"{ip}|{user_agent}|{day.isoformat()}|{settings.SECRET_KEY}"
    return hashlib.sha256(raw.encode("utf-8", "replace")).hexdigest()[:32]


class VisitLogMiddleware:
    """Record one VisitLog row per successful, human, public GET request.

    Logging is wrapped in a broad try/except: analytics must NEVER break or slow
    the actual response. Any failure (e.g. DB locked, missing table during a
    migration window) is swallowed and the response is returned unchanged.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        try:
            self._log(request, response)
        except Exception:
            pass
        return response

    def _log(self, request, response):
        path = request.path

        # settings.ADMIN_URL is normalised to "<prefix>/"; strip the trailing
        # slash and prepend "/" to get the path prefix ("/kirma-bu-yerga").
        admin_prefix = "/" + settings.ADMIN_URL.rstrip("/")
        if path.startswith(admin_prefix):
            return
        if any(path.startswith(prefix) for prefix in SKIP_PREFIXES):
            return
        if request.method != "GET":
            return
        if response.status_code >= 400:
            return
        # Don't count internal traffic: logged-in staff browsing the live site
        # (this middleware runs after AuthenticationMiddleware, so user is set).
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated and user.is_staff:
            return

        # Trusted-proxy-aware: read the real client IP from the RIGHT of
        # X-Forwarded-For so a forged prefix cannot spoof the logged IP/country.
        # Private/loopback visitors (dev machine, LAN, health checks) are kept
        # but tagged as "Local" instead of being dropped — they are real page
        # views, they just have no country to resolve.
        ip = client_ip(request)
        local = not ip or not is_public_ip(ip)

        ua_string = request.META.get("HTTP_USER_AGENT", "")
        ua = user_agents.parse(ua_string)
        # Drop known crawlers/bots — note: an empty UA is NOT a bot, so the
        # Django test client (which sends no UA) is still logged.
        if ua.is_bot:
            return

        referrer = request.META.get("HTTP_REFERER", "")

        VisitLog.objects.create(
            path=path[:512],
            method=request.method,
            referrer=referrer[:512],
            ip_address=ip or None,
            user_agent=ua_string,
            device_type=_device_type(ua),
            browser=(ua.browser.family or "")[:80],
            os=(ua.os.family or "")[:80],
            language=getattr(request, "LANGUAGE_CODE", "") or "",
            country=LOCAL_COUNTRY if local else "",
            country_code=LOCAL_CODE if local else "",
            visitor_id=visitor_hash(ip, ua_string),
        )
