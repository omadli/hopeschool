from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_ckeditor_5.fields import CKEditor5Field

from apps.common.models import TimeStampedModel, VideoMixin
from apps.common.validators import image_validators


class NewsPost(VideoMixin, TimeStampedModel):
    title = models.CharField(_("Sarlavha"), max_length=200)
    slug = models.SlugField(_("Slug"), max_length=220, unique=True)
    excerpt = models.CharField(_("Qisqa matn"), max_length=300, blank=True)
    body = CKEditor5Field(_("To'liq matn"), config_name="default", blank=True)
    cover_image = models.ImageField(_("Muqova rasmi"), upload_to="news/", blank=True,
                                    validators=image_validators)

    badge = models.CharField(_("Belgi (tag)"), max_length=40, blank=True,
                             help_text="masalan: Eʼlon, Yangilik, Tadbir")
    badge_accent = models.BooleanField(_("Qizil belgi"), default=False)

    published_at = models.DateTimeField(_("Chop etilgan sana"), default=timezone.now, db_index=True)
    is_published = models.BooleanField(_("Chop etilgan"), default=True, db_index=True)
    is_featured = models.BooleanField(_("Tanlangan"), default=False)

    meta_title = models.CharField(_("SEO sarlavha"), max_length=200, blank=True)
    meta_description = models.TextField(_("SEO tavsif"), blank=True)

    class Meta:
        # "Tanlangan" (is_featured) posts pin to the top; then newest first.
        ordering = ["-is_featured", "-published_at"]
        verbose_name = _("Yangilik / eʼlon")
        verbose_name_plural = _("Yangiliklar va eʼlonlar")

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("news:detail", kwargs={"slug": self.slug})
