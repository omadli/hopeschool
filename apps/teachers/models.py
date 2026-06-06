from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_ckeditor_5.fields import CKEditor5Field

from apps.common.models import OrderedActiveModel
from apps.common.validators import image_validators


class Teacher(OrderedActiveModel):
    full_name = models.CharField(_("F.I.Sh."), max_length=140)
    slug = models.SlugField(_("Slug"), max_length=160, unique=True)
    photo = models.ImageField(_("Rasm"), upload_to="teachers/", blank=True, validators=image_validators)
    position = models.CharField(_("Lavozim / yo'nalish"), max_length=160, blank=True)
    bio = CKEditor5Field(_("Bio / tavsif"), config_name="default", blank=True)
    subjects = models.CharField(_("Fanlar"), max_length=200, blank=True)
    experience_years = models.PositiveIntegerField(_("Tajriba (yil)"), null=True, blank=True)

    instagram_url = models.URLField(_("Instagram"), blank=True)
    telegram_url = models.URLField(_("Telegram"), blank=True)
    youtube_url = models.URLField(_("YouTube"), blank=True)

    meta_title = models.CharField(_("SEO sarlavha"), max_length=200, blank=True)
    meta_description = models.TextField(_("SEO tavsif"), blank=True)

    class Meta(OrderedActiveModel.Meta):
        verbose_name = _("O'qituvchi")
        verbose_name_plural = _("O'qituvchilar")

    def __str__(self):
        return self.full_name

    def get_absolute_url(self):
        return reverse("teachers:detail", kwargs={"slug": self.slug})
