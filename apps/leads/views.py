from urllib.parse import urlparse

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.common.utils import client_ip

from .forms import LeadForm
from .models import LeadSource

# IP rate-limit: max submissions per window (anti-flood for Telegram).
RATE_LIMIT_MAX = 5
RATE_LIMIT_WINDOW = 60 * 60  # 1 hour, seconds


def _origin_allowed(request):
    """Reject only a same-site form spoofed from another origin.

    Browsers send Origin on every fetch() POST — same-origin or not — so this
    doesn't reintroduce the reliability bug dropping CSRF fixed (unlike
    Referer, which privacy settings/extensions routinely strip). No Origin
    header at all just means a non-browser or very old client; we don't
    reject on absence, only on a mismatch.
    """
    origin = request.META.get("HTTP_ORIGIN")
    if not origin or "*" in settings.ALLOWED_HOSTS:
        return True
    host = urlparse(origin).hostname or ""
    return any(
        host == h or (h.startswith(".") and host.endswith(h))
        for h in settings.ALLOWED_HOSTS
    )


def _client_ip(request):
    """Real client IP for the per-IP rate-limit key.

    Delegates to the shared, trusted-proxy-aware ``client_ip`` (reads the real
    peer from the RIGHT of X-Forwarded-For so a forged prefix cannot bypass the
    limit); falls back to a constant bucket when no IP is available.
    """
    return client_ip(request) or "unknown"


def _capture_referrer(request):
    """Derive a referrer string from utm params or the HTTP referer."""
    utm = request.POST.get("utm_source") or request.GET.get("utm_source")
    if utm:
        return utm[:255]
    referer = request.META.get("HTTP_REFERER", "")
    return referer[:255]


@csrf_exempt
@require_POST
def lead_create(request):
    """Public lead-submission endpoint (POST /ariza/). Returns JSON.

    CSRF-exempt on purpose. This is an *anonymous* public form: there is no
    logged-in session and no per-user state for a CSRF token to protect — anyone
    may submit a lead (that is the point). Keeping CSRF on only created a
    reliability bug: a page left open long enough for its token to go stale got
    a 403 (HTML, not JSON), which the front-end surfaced as the generic
    "Ariza yuborishda xatolik" and silently dropped the submission. Abuse is
    already handled below by the Origin check, honeypot and the per-IP
    rate-limit, so dropping CSRF here costs no real protection and makes the
    form work no matter how long the visitor lingered before sending.
    """
    # 1) Cross-site spam via fetch/XHR always carries Origin — a mismatch means
    # the POST didn't come from our own page.
    if not _origin_allowed(request):
        return JsonResponse(
            {"ok": False, "error": _("Ruxsat etilmagan manba.")}, status=403
        )

    # 2) Honeypot: silently swallow spam without saving and without leaking.
    if request.POST.get("website"):
        return JsonResponse({"ok": True})

    # 3) IP rate-limit (counted only on accepted submissions, see below).
    ip = _client_ip(request)
    cache_key = f"lead_rl:{ip}"
    if (cache.get(cache_key) or 0) >= RATE_LIMIT_MAX:
        return JsonResponse(
            {"ok": False, "error": _("Juda koʻp soʻrov. Birozdan soʻng urinib koʻring.")},
            status=429,
        )

    form = LeadForm(request.POST)
    if not form.is_valid():
        return JsonResponse(
            {"ok": False, "errors": form.errors.get_json_data()}, status=400
        )

    lead = form.save(commit=False)
    lead.referrer = _capture_referrer(request)
    lead.source = LeadSource.resolve(request.POST.get("source"))
    lead.save()

    # Increment the rate-limit counter only on a successful save.
    try:
        cache.add(cache_key, 0, RATE_LIMIT_WINDOW)
        cache.incr(cache_key)
    except ValueError:
        # Key expired between add() and incr(); re-seed.
        cache.set(cache_key, 1, RATE_LIMIT_WINDOW)

    return JsonResponse({"ok": True})
