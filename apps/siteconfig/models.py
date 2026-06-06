from django.db import models
from django.utils.translation import gettext_lazy as _
from solo.models import SingletonModel

from apps.common.utils import normalize_phone
from apps.common.validators import image_validators


class SiteConfig(SingletonModel):
    """Global, admin-managed site configuration (single row)."""

    # --- Branding ---
    site_name = models.CharField(_("Sayt nomi"), max_length=120, default="Hope School")
    tagline = models.CharField(_("Shior"), max_length=200, blank=True)
    logo = models.ImageField(_("Logo"), upload_to="branding/", blank=True,
                             validators=image_validators,
                             help_text=_("Bo'sh qoldirilsa, standart logo ishlatiladi."))
    favicon = models.ImageField(_("Favicon"), upload_to="branding/", blank=True,
                                validators=image_validators)

    # --- Canonical domain (SEO uchun yagona manba) ---
    site_domain = models.CharField(
        _("Domen"), max_length=120, blank=True,
        help_text=_("Masalan: hopeschool.uz (protokolsiz). Sitemap/canonical uchun."),
    )

    # --- Contacts ---
    phone_primary = models.CharField(_("Asosiy telefon"), max_length=30, blank=True)
    phone_secondary = models.CharField(_("Qo'shimcha telefon"), max_length=30, blank=True)
    email = models.EmailField(_("Email"), blank=True)
    address = models.CharField(_("Manzil"), max_length=255, blank=True)
    working_hours = models.CharField(_("Ish vaqti"), max_length=120, blank=True)
    latitude = models.CharField(_("Kenglik (lat)"), max_length=32, blank=True)
    longitude = models.CharField(_("Uzunlik (lng)"), max_length=32, blank=True)

    # --- Maps (embed) ---
    google_maps_embed = models.TextField(_("Google Maps embed"), blank=True)
    yandex_maps_embed = models.TextField(_("Yandex Maps embed"), blank=True)

    # --- Social ---
    instagram_url = models.URLField(_("Instagram"), blank=True)
    telegram_url = models.URLField(_("Telegram kanal"), blank=True)
    telegram_group_url = models.URLField(_("Telegram guruh"), blank=True)
    youtube_url = models.URLField(_("YouTube"), blank=True)
    facebook_url = models.URLField(_("Facebook"), blank=True)
    tiktok_url = models.URLField(_("TikTok"), blank=True)

    # --- SEO defaults ---
    seo_title = models.CharField(_("SEO sarlavha"), max_length=200, blank=True)
    seo_description = models.TextField(_("SEO tavsif"), blank=True)
    og_image = models.ImageField(_("OG rasm (ulashish)"), upload_to="seo/", blank=True,
                                 validators=image_validators)

    # --- Webmaster verification ---
    google_site_verification = models.CharField(_("Google verification"), max_length=255, blank=True)
    yandex_verification = models.CharField(_("Yandex verification"), max_length=255, blank=True)
    bing_msvalidate = models.CharField(_("Bing verification"), max_length=255, blank=True)

    # --- Analytics IDs ---
    ga4_measurement_id = models.CharField(_("Google Analytics 4 ID"), max_length=40, blank=True,
                                          help_text="G-XXXXXXX")
    yandex_metrica_id = models.CharField(_("Yandex Metrica ID"), max_length=40, blank=True)

    # --- Telegram ---
    telegram_notifications_enabled = models.BooleanField(
        _("Telegram bildirishnomalari yoniq"), default=True,
    )

    class Meta:
        verbose_name = _("Sayt sozlamalari")
        verbose_name_plural = _("Sayt sozlamalari")

    def __str__(self):
        return "Sayt sozlamalari"

    def save(self, *args, **kwargs):
        self.phone_primary = normalize_phone(self.phone_primary)
        self.phone_secondary = normalize_phone(self.phone_secondary)
        super().save(*args, **kwargs)

    # --- Map helpers (auto-built from picked coordinates) ---
    @property
    def has_geo(self):
        return bool(self.latitude and self.longitude)

    @property
    def google_map_src(self):
        if self.has_geo:
            return (f"https://maps.google.com/maps?q={self.latitude},{self.longitude}"
                    f"&z=16&hl=uz&output=embed")
        return ""

    @property
    def yandex_map_src(self):
        if self.has_geo:
            return (f"https://yandex.com/map-widget/v1/?ll={self.longitude}%2C{self.latitude}"
                    f"&z=16&pt={self.longitude}%2C{self.latitude},pm2rdm")
        return ""

    @property
    def google_maps_link(self):
        if self.has_geo:
            return f"https://www.google.com/maps/search/?api=1&query={self.latitude},{self.longitude}"
        return ""

    @property
    def yandex_maps_link(self):
        if self.has_geo:
            return (f"https://yandex.com/maps/?ll={self.longitude}%2C{self.latitude}"
                    f"&z=16&pt={self.longitude}%2C{self.latitude}")
        return ""
