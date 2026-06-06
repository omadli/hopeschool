from django.core.cache import cache
from django.http import JsonResponse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from .forms import LeadForm

# IP rate-limit: max submissions per window (anti-flood for Telegram).
RATE_LIMIT_MAX = 5
RATE_LIMIT_WINDOW = 60 * 60  # 1 hour, seconds


def _client_ip(request):
    """Best-effort client IP, X-Forwarded-For aware, REMOTE_ADDR fallback."""
    xff = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "") or "unknown"


def _capture_source(request):
    """Derive a lead source string from utm params or the referrer."""
    utm = request.POST.get("utm_source") or request.GET.get("utm_source")
    if utm:
        return utm[:255]
    referer = request.META.get("HTTP_REFERER", "")
    return referer[:255]


@require_POST
def lead_create(request):
    """Public lead-submission endpoint (POST /ariza/). Returns JSON."""
    # 1) Honeypot: silently swallow spam without saving and without leaking.
    if request.POST.get("website"):
        return JsonResponse({"ok": True})

    # 2) IP rate-limit (counted only on accepted submissions, see below).
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
    lead.source = _capture_source(request)
    lead.save()

    # Increment the rate-limit counter only on a successful save.
    try:
        cache.add(cache_key, 0, RATE_LIMIT_WINDOW)
        cache.incr(cache_key)
    except ValueError:
        # Key expired between add() and incr(); re-seed.
        cache.set(cache_key, 1, RATE_LIMIT_WINDOW)

    return JsonResponse({"ok": True})
