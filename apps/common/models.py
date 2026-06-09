from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.validators import video_validators


class VideoMixin(models.Model):
    """Optional video on any content model: a YouTube/Vimeo/embed URL OR an
    uploaded file. The URL takes precedence when both are set."""

    video_url = models.URLField(
        _("Video havola"), blank=True,
        help_text=_("YouTube, Vimeo yoki embed havola."),
    )
    video_file = models.FileField(
        _("Video fayl"), upload_to="videos/", blank=True,
        validators=video_validators,
        help_text=_("MP4/WebM. Havola berilsa, shart emas."),
    )

    class Meta:
        abstract = True

    @property
    def has_video(self):
        return bool(self.video_url or self.video_file)

    @property
    def video_embed(self):
        """Embeddable iframe src for ``video_url`` (empty if only a file)."""
        from apps.common.utils import video_embed_url
        return video_embed_url(self.video_url)


class TimeStampedModel(models.Model):
    """Abstract base: created/updated timestamps."""

    created_at = models.DateTimeField(_("Yaratilgan"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Yangilangan"), auto_now=True)

    class Meta:
        abstract = True


class OrderedActiveModel(TimeStampedModel):
    """Abstract base for admin-managed content: ordering + visibility.

    Every content model (courses, teachers, gallery, etc.) inherits this so the
    admin can reorder items and hide them from the site without deleting.
    """

    order = models.PositiveIntegerField(
        _("Tartib raqami"), default=0, db_index=True,
        help_text=_("Kichik raqam yuqorida ko'rinadi."),
    )
    is_active = models.BooleanField(
        _("Saytda ko'rsatilsin"), default=True, db_index=True,
    )

    class Meta:
        abstract = True
        ordering = ["order", "-created_at"]
