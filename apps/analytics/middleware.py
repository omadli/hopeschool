import user_agents

from .models import VisitLog

# Path prefixes that should never be logged as a public page visit.
SKIP_PREFIXES = (
    "/admin",
    "/static",
    "/media",
    "/favicon",
    "/i18n",
    "/ckeditor5",
)


def _client_ip(request):
    """Return the originating client IP.

    Honours the first hop of X-Forwarded-For (set by a trusted reverse proxy)
    and falls back to REMOTE_ADDR for direct connections.
    """
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR") or None


def _device_type(ua):
    if ua.is_mobile:
        return VisitLog.DeviceType.MOBILE
    if ua.is_tablet:
        return VisitLog.DeviceType.TABLET
    if ua.is_pc:
        return VisitLog.DeviceType.DESKTOP
    return VisitLog.DeviceType.OTHER


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

        if any(path.startswith(prefix) for prefix in SKIP_PREFIXES):
            return
        if request.method != "GET":
            return
        if response.status_code >= 400:
            return

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
            ip_address=_client_ip(request),
            user_agent=ua_string,
            device_type=_device_type(ua),
            browser=(ua.browser.family or "")[:80],
            os=(ua.os.family or "")[:80],
            language=getattr(request, "LANGUAGE_CODE", "") or "",
        )
