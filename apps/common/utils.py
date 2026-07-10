import ipaddress
import re

from django.conf import settings


def is_public_ip(ip):
    """True only for routable public addresses (skip private/loopback/etc.).

    Shared helper used by the analytics geo-IP resolver and the certificate
    importer's SSRF guard, so both agree on what counts as an internal address.
    """
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return not (
        addr.is_private
        or addr.is_loopback
        or addr.is_reserved
        or addr.is_link_local
        or addr.is_multicast
        or addr.is_unspecified
    )


def client_ip(request):
    """Return the real client IP, resilient to a forged X-Forwarded-For.

    nginx *appends* the peer it actually saw, so the trustworthy entry sits
    ``TRUSTED_PROXY_COUNT`` hops from the END of X-Forwarded-For; the leftmost
    entries are attacker-controlled. Reading from the right is what stops a
    client from spoofing its IP to bypass the lead rate-limit or poison the
    analytics geo data. Single source of truth for both call sites.
    """
    xff = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if xff:
        parts = [p.strip() for p in xff.split(",") if p.strip()]
        if parts:
            hops = getattr(settings, "TRUSTED_PROXY_COUNT", 1)
            return parts[-min(hops, len(parts))]
    return request.META.get("REMOTE_ADDR", "") or ""


def normalize_phone(value):
    """Normalize an Uzbek phone to '+998XXXXXXXXX' (12 digits after +).

    Strips spaces, dashes, parentheses. Accepts 9-digit local numbers and
    prepends 998. Returns the value unchanged if it can't be normalized.
    """
    if not value:
        return value
    digits = re.sub(r"\D", "", str(value))
    if digits.startswith("00998"):
        digits = digits[2:]
    if len(digits) == 9:           # 901234567 -> 998901234567
        digits = "998" + digits
    if len(digits) == 12 and digits.startswith("998"):
        return "+" + digits
    return value  # leave as-is if unexpected format


def video_embed_url(url):
    """Convert a YouTube/Vimeo watch URL to an embeddable iframe ``src``.

    Returns an already-embeddable URL unchanged, recognises the common YouTube
    (watch / youtu.be / shorts) and Vimeo forms, and falls back to the original
    URL for anything else (best effort — admins can paste a raw embed link).

    Note: a watch URL where ``v=`` is not the first query param
    (e.g. ``watch?list=...&v=ID``) is not matched and passes through; uncommon
    for pasted share links, and the admin previews the result visually.
    """
    if not url:
        return ""
    url = url.strip()
    if "/embed/" in url or "player.vimeo.com" in url:
        return url
    m = re.search(r"(?:youtube\.com/(?:watch\?v=|shorts/)|youtu\.be/)([\w-]{11})", url)
    if m:
        return f"https://www.youtube.com/embed/{m.group(1)}"
    m = re.search(r"vimeo\.com/(?:video/)?(\d+)", url)
    if m:
        return f"https://player.vimeo.com/video/{m.group(1)}"
    return url
