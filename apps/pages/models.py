from django.db import models
from django.utils.translation import gettext_lazy as _
from django_ckeditor_5.fields import CKEditor5Field

from apps.common.constants import ICON_CHOICES
from apps.common.models import OrderedActiveModel
from apps.common.validators import image_validators


class AboutSection(OrderedActiveModel):
    """'Biz haqimizda' bo'limining matni (birinchi faol yozuv ko'rsatiladi)."""

    title = models.CharField(_("Sarlavha"), max_length=200)
    subtitle = models.CharField(_("Kichik sarlavha"), max_length=200, blank=True)
    body = CKEditor5Field(_("Matn"), config_name="default", blank=True)
    image = models.ImageField(_("Rasm"), upload_to="about/", blank=True, validators=image_validators)

    class Meta(OrderedActiveModel.Meta):
        verbose_name = _("Biz haqimizda bo'limi")
        verbose_name_plural = _("Biz haqimizda bo'limi")

    def __str__(self):
        return self.title


class StatItem(OrderedActiveModel):
    """Statistika raqamlari (hero bo'limida counter bilan)."""

    number = models.PositiveIntegerField(_("Raqam"), default=0)
    suffix = models.CharField(_("Belgi"), max_length=8, blank=True, help_text="+, %, k …")
    label = models.CharField(_("Izoh"), max_length=80)
    accent = models.BooleanField(_("Qizil rang bilan"), default=False)

    class Meta(OrderedActiveModel.Meta):
        verbose_name = _("Statistika raqami")
        verbose_name_plural = _("Statistika raqamlari")

    def __str__(self):
        return f"{self.number}{self.suffix} — {self.label}"


class WhyUsItem(OrderedActiveModel):
    """'Nega biz' kartalari."""

    title = models.CharField(_("Sarlavha"), max_length=120)
    description = models.TextField(_("Tavsif"), blank=True)
    icon = models.CharField(_("Ikonka"), max_length=20, choices=ICON_CHOICES, default="cap")
    accent = models.BooleanField(_("Qizil ikonka"), default=False)

    class Meta(OrderedActiveModel.Meta):
        verbose_name = _("Nega biz — karta")
        verbose_name_plural = _("Nega biz — kartalar")

    def __str__(self):
        return self.title
