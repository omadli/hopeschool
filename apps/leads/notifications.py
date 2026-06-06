"""Telegram notification for new leads.

`notify_new_lead` is the *synchronous* worker. The post_save signal runs it
inside a daemon thread (after transaction commit), so the request is never
delayed and an HTTP/network failure can never break the user's submission.
"""
import html
import logging

import requests
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


def _build_message(lead):
    """Render a tidy HTML message body (parse_mode=HTML)."""
    course = html.escape(str(lead.course)) if lead.course else "—"
    message = html.escape(lead.message) if lead.message else "—"
    created = timezone.localtime(lead.created_at).strftime("%d.%m.%Y %H:%M")
    lines = [
        "<b>🆕 Yangi ariza</b>",
        "",
        f"👤 <b>Ism:</b> {html.escape(lead.full_name)}",
        f"📞 <b>Telefon:</b> {html.escape(lead.phone)}",
        f"📚 <b>Kurs:</b> {course}",
        f"💬 <b>Izoh:</b> {message}",
        f"🕒 <b>Vaqt:</b> {created}",
    ]
    return "\n".join(lines)


def notify_new_lead(lead):
    """Send a Telegram message about a new lead. Never raises.

    Guards short-circuit before touching the DB so an empty token costs nothing.
    """
    token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_ADMIN_CHAT_ID
    if not token or not chat_id:
        return

    # Runtime on/off switch from the singleton SiteConfig.
    try:
        from apps.siteconfig.models import SiteConfig
        if not SiteConfig.get_solo().telegram_notifications_enabled:
            return
    except Exception:  # pragma: no cover - defensive
        logger.exception("Lead notify: could not read SiteConfig")
        return

    try:
        resp = requests.post(
            TELEGRAM_API.format(token=token),
            json={
                "chat_id": chat_id,
                "text": _build_message(lead),
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
            timeout=5,
        )
        if resp.status_code == 200:
            lead.is_notified = True
            lead.save(update_fields=["is_notified", "updated_at"])
        else:
            logger.warning(
                "Lead notify: Telegram returned %s: %s",
                resp.status_code, resp.text[:300],
            )
    except Exception:
        logger.exception("Lead notify: failed to send Telegram message")
