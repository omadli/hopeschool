from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import TimeStampedModel
from apps.common.utils import normalize_phone


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
    source = models.CharField(
        _("Manba"), max_length=255, blank=True,
        help_text=_("UTM yoki referrer (avtomatik toʻldiriladi)."),
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
