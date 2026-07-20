from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import OrderedActiveModel
from apps.common.validators import image_validators


class Testimonial(OrderedActiveModel):
    author_name = models.CharField(_("Muallif"), max_length=120)
    author_role = models.CharField(_("Roli"), max_length=120, blank=True,
                                   help_text="masalan: Ona · Aziza R.")
    content = models.TextField(_("Fikr matni"))
    photo = models.ImageField(_("Rasm"), upload_to="testimonials/", blank=True,
                              validators=image_validators)
    rating = models.PositiveSmallIntegerField(_("Baho (1–5)"), null=True, blank=True)
    is_featured = models.BooleanField(_("Tanlangan"), default=False)

    class Meta(OrderedActiveModel.Meta):
        # "Tanlangan" (is_featured) fikrlar tepaga chiqadi, keyin qo‘lda tartib.
        ordering = ["-is_featured", "order", "-created_at"]
        verbose_name = _("Fikr")
        verbose_name_plural = _("Fikrlar (ota-onalar)")

    def __str__(self):
        return self.author_name
