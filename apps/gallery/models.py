from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import OrderedActiveModel, VideoMixin
from apps.common.validators import image_validators


class GalleryAlbum(OrderedActiveModel):
    title = models.CharField(_("Albom nomi"), max_length=140)
    slug = models.SlugField(_("Slug"), max_length=160, unique=True)
    description = models.CharField(_("Tavsif"), max_length=255, blank=True)
    cover_image = models.ImageField(_("Muqova rasmi"), upload_to="gallery/covers/", blank=True,
                                    validators=image_validators)

    class Meta(OrderedActiveModel.Meta):
        verbose_name = _("Galereya albomi")
        verbose_name_plural = _("Galereya albomlari")

    def __str__(self):
        return self.title


class GalleryImage(OrderedActiveModel):
    album = models.ForeignKey(
        GalleryAlbum, on_delete=models.CASCADE, related_name="images",
        verbose_name=_("Albom"), null=True, blank=True,
    )
    image = models.ImageField(_("Rasm"), upload_to="gallery/", validators=image_validators)
    caption = models.CharField(_("Izoh"), max_length=200, blank=True)
    alt_text = models.CharField(_("ALT matn (SEO)"), max_length=200, blank=True)

    class Meta(OrderedActiveModel.Meta):
        verbose_name = _("Galereya rasmi")
        verbose_name_plural = _("Galereya rasmlari")

    def __str__(self):
        return self.caption or f"Rasm #{self.pk}"


class GalleryVideo(VideoMixin, OrderedActiveModel):
    """A video (YouTube/embed or uploaded) shown in the gallery."""

    album = models.ForeignKey(
        GalleryAlbum, on_delete=models.CASCADE, related_name="videos",
        verbose_name=_("Albom"), null=True, blank=True,
    )
    title = models.CharField(_("Sarlavha"), max_length=200, blank=True)
    thumbnail = models.ImageField(
        _("Muqova rasmi"), upload_to="gallery/video_covers/", blank=True,
        validators=image_validators,
        help_text=_("Ixtiyoriy — yuklangan video uchun muqova."),
    )

    class Meta(OrderedActiveModel.Meta):
        verbose_name = _("Galereya videosi")
        verbose_name_plural = _("Galereya videolari")

    def __str__(self):
        return self.title or f"Video #{self.pk}"
