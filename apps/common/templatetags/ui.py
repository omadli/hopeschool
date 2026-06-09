import re

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def phone_display(value):
    """'+998901234567' -> '+998 90 123 45 67'."""
    if not value:
        return value
    d = re.sub(r"\D", "", str(value))
    if len(d) == 12 and d.startswith("998"):
        return f"+{d[0:3]} {d[3:5]} {d[5:8]} {d[8:10]} {d[10:12]}"
    return value

# Inner SVG paths (viewBox 0 0 24 24, stroke-based line icons)
ICONS = {
    "cap": '<path d="M12 3 1.5 8 12 13l8.5-4.05V14"/><path d="M5.5 10.5V15c0 1.2 2.9 2.5 6.5 2.5s6.5-1.3 6.5-2.5v-4.5"/>',
    "users": '<path d="M12 14c-4 0-7 2-7 5h14c0-3-3-5-7-5z"/><circle cx="12" cy="8" r="4"/>',
    "method": '<path d="M12 2v3M12 19v3M2 12h3M19 12h3"/><circle cx="12" cy="12" r="4"/>',
    "group": '<circle cx="9" cy="8" r="3"/><circle cx="17" cy="9" r="2.4"/><path d="M3 19c0-3 2.5-5 6-5s6 2 6 5"/>',
    "shield": '<path d="m9 12 2 2 4-4"/><path d="M12 3 4 6v6c0 5 3.5 7.5 8 9 4.5-1.5 8-4 8-9V6z"/>',
    "book": '<path d="M4 5h11a4 4 0 0 1 4 4v10a3 3 0 0 0-3-3H4z"/><path d="M20 5h-1a4 4 0 0 0-4 4v10"/>',
    "calc": '<path d="M4 4h16v16H4z"/><path d="M8 9h8M8 13h5"/>',
    "code": '<path d="m8 9-3 3 3 3M16 9l3 3-3 3M13 6l-2 12"/>',
    "chart": '<path d="M12 20V10M6 20V4M18 20v-7"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "star": '<path d="M12 3l2.6 5.3 5.9.9-4.2 4.1 1 5.8L12 16.9 6.7 19l1-5.8L3.5 9.2l5.9-.9z"/>',
    "location": '<path d="M12 21s-7-5.5-7-11a7 7 0 0 1 14 0c0 5.5-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/>',
    "phone": '<path d="M22 16.9v3a2 2 0 0 1-2.2 2A19.8 19.8 0 0 1 2.1 4.1 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7l.7 2.9a2 2 0 0 1-.5 2.1L8.1 9.9a16 16 0 0 0 6 6l1.2-1.2a2 2 0 0 1 2.1-.5l2.9.7A2 2 0 0 1 22 16.9z"/>',
    "language": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 2.7 2.5 15.3 0 18M12 3c-2.5 2.7-2.5 15.3 0 18"/>',
}


@register.simple_tag
def icon(name, size=22, cls=""):
    inner = ICONS.get(name or "", ICONS["cap"])
    return mark_safe(
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        f'stroke="currentColor" stroke-width="1.9" class="{cls}">{inner}</svg>'
    )


# Brand icons (fill-based, viewBox 0 0 24 24) keyed by SocialLink.platform.
SOCIAL_ICONS = {
    "instagram": '<path d="M7 2C4.2 2 2 4.2 2 7v10c0 2.8 2.2 5 5 5h10c2.8 0 5-2.2 5-5V7c0-2.8-2.2-5-5-5H7zm10 2c.6 0 1 .4 1 1s-.4 1-1 1-1-.4-1-1 .4-1 1-1zM12 7a5 5 0 1 1 0 10 5 5 0 0 1 0-10zm0 2a3 3 0 1 0 0 6 3 3 0 0 0 0-6z"/>',
    "telegram": '<path d="M21.9 4.3 18.6 20c-.2 1-.9 1.3-1.8.8l-4.9-3.6-2.4 2.3c-.3.3-.5.5-1 .5l.4-5 9.1-8.2c.4-.4-.1-.6-.6-.2L6.6 13.4l-4.8-1.5c-1-.3-1-1 .2-1.5l18.7-7.2c.9-.3 1.6.2 1.3 1.6z"/>',
    "youtube": '<path d="M21.9 5.6c-.2-.9-1-1.5-1.9-1.6C17.9 3.7 12 3.7 12 3.7s-5.9 0-8 .3C3.1 4.1 2.3 4.7 2.1 5.6 1.8 7.4 1.8 12 1.8 12s0 4.6.3 6.4c.2.9 1 1.5 1.9 1.6 2.1.3 8 .3 8 .3s5.9 0 8-.3c.9-.1 1.7-.7 1.9-1.6.3-1.8.3-6.4.3-6.4s0-4.6-.3-6.4zM10 15.2V8.8l5.2 3.2L10 15.2z"/>',
    "facebook": '<path d="M22 12a10 10 0 1 0-11.6 9.9v-7H7.9V12h2.5V9.8c0-2.5 1.5-3.9 3.8-3.9 1.1 0 2.2.2 2.2.2v2.5h-1.3c-1.2 0-1.6.8-1.6 1.6V12h2.8l-.4 2.9h-2.3v7A10 10 0 0 0 22 12z"/>',
    "tiktok": '<path d="M16.6 5.8c-.9-.6-1.5-1.6-1.7-2.8h-2.7v11.2a2.3 2.3 0 1 1-2-2.3V9.2a5 5 0 1 0 4.7 5V8.6a6 6 0 0 0 3.6 1.2V7.1c-.7 0-1.4-.2-1.9-.6z"/>',
    "twitter": '<path d="M18.2 3h3.3l-7.2 8.2L23 21h-6.6l-5.2-6.8L5.3 21H2l7.7-8.8L1.5 3h6.8l4.7 6.2L18.2 3zm-1.2 16h1.8L7.1 4.9H5.2L17 19z"/>',
    "linkedin": '<path d="M4.98 3.5a2.5 2.5 0 1 1 0 5 2.5 2.5 0 0 1 0-5zM3 9h4v12H3V9zm6 0h3.8v1.7h.1c.5-1 1.8-2 3.7-2 4 0 4.7 2.6 4.7 6V21h-4v-5.3c0-1.3 0-3-1.8-3s-2.1 1.4-2.1 2.9V21H9V9z"/>',
    "whatsapp": '<path d="M12 2a10 10 0 0 0-8.5 15.3L2 22l4.8-1.5A10 10 0 1 0 12 2zm0 18a8 8 0 0 1-4.1-1.1l-.3-.2-2.9.9.8-2.8-.2-.3A8 8 0 1 1 12 20zm4.5-6c-.2-.1-1.5-.7-1.7-.8s-.4-.1-.5.1-.6.8-.8 1-.3.2-.5.1a6.6 6.6 0 0 1-3.3-2.9c-.2-.4.2-.4.6-1.2.1-.1 0-.3 0-.4l-.7-1.7c-.2-.4-.4-.4-.5-.4h-.5a.9.9 0 0 0-.7.3 2.8 2.8 0 0 0-.9 2.1c0 1.2.9 2.4 1 2.6.1.2 1.8 2.7 4.3 3.8 1.6.7 2.2.7 3 .6.5-.1 1.5-.6 1.7-1.2.2-.6.2-1.1.1-1.2s-.2-.2-.4-.3z"/>',
    "website": '<path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zm6.9 6h-2.8a15.7 15.7 0 0 0-1.2-3.4A8 8 0 0 1 18.9 8zM12 4c.8 1.1 1.4 2.5 1.8 4h-3.6c.4-1.5 1-2.9 1.8-4zM4.3 14a8 8 0 0 1 0-4h3.2a16.5 16.5 0 0 0 0 4H4.3zm.8 2h2.8c.3 1.2.7 2.4 1.2 3.4A8 8 0 0 1 5.1 16zm2.8-8H5.1a8 8 0 0 1 4-3.4C8.6 5.6 8.2 6.8 7.9 8zM12 20c-.8-1.1-1.4-2.5-1.8-4h3.6c-.4 1.5-1 2.9-1.8 4zm2.3-6H9.7a14.7 14.7 0 0 1 0-4h4.6a14.7 14.7 0 0 1 0 4zm.6 5.4c.5-1 .9-2.2 1.2-3.4h2.8a8 8 0 0 1-4 3.4zm1.6-5.4a16.5 16.5 0 0 0 0-4h3.2a8 8 0 0 1 0 4h-3.2z"/>',
}


@register.simple_tag
def social_icon(platform, size=16, cls=""):
    """Brand SVG for a SocialLink platform (falls back to a generic website icon)."""
    inner = SOCIAL_ICONS.get(platform or "", SOCIAL_ICONS["website"])
    return mark_safe(
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" '
        f'fill="currentColor" class="{cls}">{inner}</svg>'
    )


@register.filter
def som(value):
    """Format a number with thin spaces: 600000 -> '600 000'."""
    try:
        return "{:,}".format(int(value)).replace(",", " ")
    except (TypeError, ValueError):
        return value


_YANDEX_LOCALE = {"uz": "uz_UZ", "ru": "ru_RU", "en": "en_US"}


@register.simple_tag
def google_map_src(config, lang="uz"):
    if config and config.latitude and config.longitude:
        return (f"https://www.google.com/maps?q={config.latitude},{config.longitude}"
                f"&z=16&hl={lang}&output=embed")
    return ""


@register.simple_tag
def yandex_map_src(config, lang="uz"):
    if config and config.latitude and config.longitude:
        loc = _YANDEX_LOCALE.get(lang, "uz_UZ")
        return (f"https://yandex.uz/map-widget/v1/?ll={config.longitude}%2C{config.latitude}"
                f"&z=16&lang={loc}&pt={config.longitude}%2C{config.latitude},pm2rdm")
    return ""
