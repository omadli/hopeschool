import re


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
