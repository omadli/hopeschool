"""Telegram notification for new leads.

`notify_new_lead` is the *synchronous* worker. The post_save signal runs it
inside a daemon thread (after transaction commit), so the request is never
delayed and an HTTP/network failure can never break the user's submission.

The bot token and the list of admin recipients are managed from the Django
admin (``SiteConfig.telegram_bot_token`` + ``TelegramRecipient`` rows). The
``.env`` values (``TELEGRAM_BOT_TOKEN`` / ``TELEGRAM_ADMIN_CHAT_ID``) stay as a
fallback so existing deployments keep delivering until the panel is filled in.
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


def _resolve_config():
    """Return ``(token, [chat_ids])`` from the admin panel, ``.env`` as fallback.

    Returns ``(None, [])`` when notifications are switched off or nothing is
    configured, so the caller can short-circuit before touching the network.
    """
    try:
        from apps.siteconfig.models import SiteConfig, TelegramRecipient
        config = SiteConfig.get_solo()
        if not config.telegram_notifications_enabled:
            return None, []
        token = (config.telegram_bot_token or settings.TELEGRAM_BOT_TOKEN or "").strip()
        chat_ids = list(
            TelegramRecipient.objects.filter(is_active=True)
            .values_list("chat_id", flat=True)
        )
    except Exception:  # pragma: no cover - defensive
        logger.exception("Lead notify: could not read Telegram config")
        return None, []

    # Backwards-compat: with no recipients added in the admin yet, fall back to
    # the single .env chat id so an upgrade keeps delivering out of the box.
    if not chat_ids and settings.TELEGRAM_ADMIN_CHAT_ID:
        chat_ids = [settings.TELEGRAM_ADMIN_CHAT_ID]

    chat_ids = [c.strip() for c in chat_ids if c and c.strip()]
    return (token or None), chat_ids


def _send(token, chat_id, text):
    """POST one message to ``chat_id``. Returns True on HTTP 200, never raises."""
    try:
        resp = requests.post(
            TELEGRAM_API.format(token=token),
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
            timeout=5,
        )
        if resp.status_code == 200:
            return True
        logger.warning(
            "Lead notify: Telegram returned %s for chat %s: %s",
            resp.status_code, chat_id, resp.text[:300],
        )
    except Exception:
        logger.exception("Lead notify: failed to send to chat %s", chat_id)
    return False


def notify_new_lead(lead):
    """Notify every active admin about a new lead. Never raises.

    The lead is marked ``is_notified`` as long as *at least one* recipient was
    reached, so a single bad chat id does not hide an otherwise delivered ariza.
    """
    token, chat_ids = _resolve_config()
    if not token or not chat_ids:
        return

    text = _build_message(lead)
    sent_any = False
    for chat_id in chat_ids:
        if _send(token, chat_id, text):
            sent_any = True

    if sent_any:
        lead.is_notified = True
        lead.save(update_fields=["is_notified", "updated_at"])
