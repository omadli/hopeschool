from django.db import models
from django.utils.translation import gettext_lazy as _


class VisitLog(models.Model):
    """A single page view captured by VisitLogMiddleware.

    Bots, admin/static/media paths and error responses are filtered out by the
    middleware before a row is created, so this table holds real human GET
    visits to public pages only.
    """

    class DeviceType(models.TextChoices):
        MOBILE = "mobile", _("Telefon")
        TABLET = "tablet", _("Planshet")
        DESKTOP = "desktop", _("Kompyuter")
        BOT = "bot", _("Bot")
        OTHER = "other", _("Boshqa")

    path = models.CharField(_("Manzil"), max_length=512, db_index=True)
    method = models.CharField(_("Metod"), max_length=8)
    referrer = models.CharField(_("Yoʻnaltiruvchi"), max_length=512, blank=True)
    ip_address = models.GenericIPAddressField(
        _("IP manzil"), null=True, blank=True, db_index=True
    )
    user_agent = models.TextField(_("Brauzer maʼlumoti"), blank=True)
    device_type = models.CharField(
        _("Qurilma turi"),
        max_length=10,
        choices=DeviceType.choices,
        default=DeviceType.OTHER,
        db_index=True,
    )
    browser = models.CharField(_("Brauzer"), max_length=80, blank=True)
    os = models.CharField(_("Operatsion tizim"), max_length=80, blank=True)
    language = models.CharField(_("Til"), max_length=8, blank=True)
    # Geo (resolved out-of-band by the resolve_geoip management command, never
    # in the request path). Empty until resolved; private/local IPs stay empty.
    country = models.CharField(_("Davlat"), max_length=80, blank=True, db_index=True)
    # ISO 3166-1 alpha-2, or "ZZ" for traffic from a private/loopback address
    # (dev machine, LAN, health check) — those can never be geolocated.
    country_code = models.CharField(_("Davlat kodi"), max_length=2, blank=True)
    # Rotating per-day pseudonymous visitor hash (IP + UA + SECRET_KEY + date).
    # Lets the dashboard count "users", sessions, bounce rate and visit duration
    # without a cookie and without storing anything re-identifiable.
    visitor_id = models.CharField(
        _("Tashrifchi"), max_length=32, blank=True, db_index=True
    )
    created_at = models.DateTimeField(_("Vaqti"), auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = _("Tashrif")
        verbose_name_plural = _("Tashriflar")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["created_at", "device_type"]),
            models.Index(fields=["created_at", "path"]),
        ]

    def __str__(self):
        return f"{self.path} — {self.created_at:%Y-%m-%d %H:%M}"
