from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .forms import LeadForm
from .models import LeadSource

# IP rate-limit: max submissions per window (anti-flood for Telegram).
RATE_LIMIT_MAX = 5
RATE_LIMIT_WINDOW = 60 * 60  # 1 hour, seconds


def _client_ip(request):
    """Real client IP, resilient to a forged X-Forwarded-For.

    nginx forwards ``X-Forwarded-For: <client-supplied…>, <real peer>`` — it
    *appends* the peer it actually saw. The leftmost entries are attacker-
    controlled, so we must read from the RIGHT: the real client sits
    ``TRUSTED_PROXY_COUNT`` hops from the end (nginx = 1, +1 for a CDN/WAF).
    Taking ``[0]`` here would let anyone bypass the rate-limit by rotating a
    fake first entry on every request.
    """
    xff = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if xff:
        parts = [p.strip() for p in xff.split(",") if p.strip()]
        if parts:
            hops = getattr(settings, "TRUSTED_PROXY_COUNT", 1)
            return parts[-min(hops, len(parts))]
    return request.META.get("REMOTE_ADDR", "") or "unknown"


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
    already handled below by the honeypot and the per-IP rate-limit, so dropping
    CSRF here costs no real protection and makes the form work no matter how long
    the visitor lingered before sending.
    """
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
