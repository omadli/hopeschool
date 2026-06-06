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
