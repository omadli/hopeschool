from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import OrderedActiveModel, TimeStampedModel
from apps.common.utils import normalize_phone
from apps.common.validators import image_validators

# Slugs that render as an existing brand icon (see social_icon template tag).
# 'site' shows the generic website glyph.
_BRAND_SLUGS = {
    "site": "website", "telegram": "telegram", "instagram": "instagram",
    "facebook": "facebook", "youtube": "youtube", "tiktok": "tiktok",
    "twitter": "twitter", "linkedin": "linkedin", "whatsapp": "whatsapp",
}


class LeadSource(OrderedActiveModel):
    """An ad channel a lead can arrive from (site, telegram, instagram, …).

    Drives the hidden ``source`` field on the public form and the CRM stats
    block. Built-in channels are ``is_protected`` so they cannot be deleted or
    re-slugged — their slugs are baked into shared ad links."""

    DEFAULT_SLUG = "site"

    name = models.CharField(_("Nomi"), max_length=80)
    slug = models.SlugField(_("Slug"), max_length=80, unique=True)
    icon = models.CharField(
        _("Ikonka"), max_length=48, blank=True,
        help_text=_("Material Symbols nomi (masalan: public). Rasm boʻlmaganda ishlatiladi."),
    )
    image = models.ImageField(
        _("Rasm (hisobot uchun)"), upload_to="crm/sources/", blank=True,
        validators=image_validators,
    )
    color = models.CharField(
        _("Rang"), max_length=7, blank=True,
        help_text=_("#RRGGBB. Boʻsh boʻlsa asosiy rang ishlatiladi."),
    )
    is_protected = models.BooleanField(_("Himoyalangan"), default=False, editable=False)

    class Meta(OrderedActiveModel.Meta):
        verbose_name = _("Manba")
        verbose_name_plural = _("Manbalar")

    def __str__(self):
        return self.name

    @property
    def brand_key(self):
        """social_icon platform key for this slug, or '' if not a known brand."""
        return _BRAND_SLUGS.get(self.slug, "")

    def build_link(self, domain, lang):
        """Absolute application link in ``lang`` carrying this source slug."""
        domain = (domain or "").strip().rstrip("/")
        return f"https://{domain}/{lang}/#contact?source={self.slug}"

    @classmethod
    def get_default(cls):
        """The 'site' channel; created on the fly if it was ever removed."""
        obj, _created = cls.objects.get_or_create(
            slug=cls.DEFAULT_SLUG,
            defaults={"name": "Sayt", "icon": "public", "is_protected": True},
        )
        return obj

    @classmethod
    def resolve(cls, slug):
        """Active source matching ``slug``; the default 'site' source otherwise."""
        if slug:
            match = cls.objects.filter(slug=slug, is_active=True).first()
            if match:
                return match
        return cls.get_default()


class Lead(TimeStampedModel):
    """A site visitor's application (ariza) — captured from the lead forms."""

    class Status(models.TextChoices):
        NEW = "new", _("Yangi")
        CONTACTED = "contacted", _("Bogʻlanildi")
        ENROLLED = "enrolled", _("Oʻquvchi boʻldi")
        REJECTED = "rejected", _("Rad etildi")

    full_name = models.CharField(_("Ism familiya"), max_length=140)
    phone = models.CharField(_("Telefon"), max_length=20)
    course = models.ForeignKey(
        "courses.Course", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="leads", verbose_name=_("Kurs"),
    )
    message = models.TextField(_("Izoh"), blank=True)
    referrer = models.CharField(
        _("Referrer"), max_length=255, blank=True,
        help_text=_("UTM yoki referrer (avtomatik toʻldiriladi)."),
    )
    source = models.ForeignKey(
        "leads.LeadSource", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="leads", verbose_name=_("Manba"),
    )
    status = models.CharField(
        _("Holat"), max_length=20, choices=Status.choices,
        default=Status.NEW, db_index=True,
    )
    is_notified = models.BooleanField(
        _("Telegramga yuborildi"), default=False,
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Ariza")
        verbose_name_plural = _("Arizalar")

    def __str__(self):
        return f"{self.full_name} — {self.phone}"

    def save(self, *args, **kwargs):
        self.phone = normalize_phone(self.phone)
        super().save(*args, **kwargs)
