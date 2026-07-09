from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import OrderedActiveModel
from apps.common.validators import image_validators, pdf_validators


class Certificate(OrderedActiveModel):
    title = models.CharField(_("Sarlavha"), max_length=160)
    student_name = models.CharField(_("O'quvchi ismi"), max_length=140, blank=True)
    description = models.CharField(_("Izoh"), max_length=200, blank=True,
                                   help_text="masalan: IELTS Band 7.5")
    badge = models.CharField(_("Belgi"), max_length=40, blank=True, help_text="masalan: IELTS, SAT")
    badge_accent = models.BooleanField(_("Qizil belgi"), default=False)

    image = models.ImageField(_("Rasm"), upload_to="certificates/", blank=True,
                              validators=image_validators)
    pdf_file = models.FileField(_("PDF fayl"), upload_to="certificates/pdf/", blank=True,
                                validators=pdf_validators)
    external_url = models.URLField(_("Tashqi havola"), blank=True)
    issued_on = models.DateField(_("Sertifikat olingan sanasi"), null=True, blank=True,
                                 help_text=_("PDF havoladan avtomatik aniqlanadi (topilsa)."))

    class Meta(OrderedActiveModel.Meta):
        verbose_name = _("Sertifikat")
        verbose_name_plural = _("Sertifikatlar")

    def __str__(self):
        return self.title

    def clean(self):
        if not (self.image or self.pdf_file or self.external_url):
            raise ValidationError(
                _("Rasm, PDF yoki tashqi havoladan kamida bittasini kiriting.")
            )

    @property
    def link(self):
        """Where the certificate card points (image > pdf > url)."""
        if self.external_url:
            return self.external_url
        if self.pdf_file:
            return self.pdf_file.url
        if self.image:
            return self.image.url
        return ""
