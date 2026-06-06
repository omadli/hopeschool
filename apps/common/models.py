from django.db import models
from django.utils.translation import gettext_lazy as _


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
