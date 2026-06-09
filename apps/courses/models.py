from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_ckeditor_5.fields import CKEditor5Field

from apps.common.constants import ICON_CHOICES
from apps.common.models import OrderedActiveModel, VideoMixin
from apps.common.validators import image_validators


class CourseCategory(OrderedActiveModel):
    name = models.CharField(_("Nomi"), max_length=80)
    slug = models.SlugField(_("Slug"), max_length=90, unique=True)

    class Meta(OrderedActiveModel.Meta):
        verbose_name = _("Kurs turkumi")
        verbose_name_plural = _("Kurs turkumlari")

    def __str__(self):
        return self.name


class Course(VideoMixin, OrderedActiveModel):
    category = models.ForeignKey(
        CourseCategory, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="courses", verbose_name=_("Turkum"),
    )
    name = models.CharField(_("Nomi"), max_length=140)
    slug = models.SlugField(_("Slug"), max_length=160, unique=True)
    short_description = models.CharField(_("Qisqa tavsif"), max_length=255, blank=True)
    description = CKEditor5Field(_("To'liq tavsif"), config_name="default", blank=True)

    duration_text = models.CharField(_("Davomiyligi"), max_length=60, blank=True, help_text="masalan: 6 oy")
    group_size = models.CharField(_("Guruh hajmi"), max_length=40, blank=True, help_text="masalan: 6–10")

    price = models.DecimalField(_("Narx"), max_digits=12, decimal_places=0, null=True, blank=True)
    price_note = models.CharField(_("Narx izohi"), max_length=40, blank=True, help_text="masalan: so'm/oy")
    is_price_visible = models.BooleanField(_("Narx ko'rsatilsin"), default=True)

    icon = models.CharField(_("Ikonka"), max_length=20, choices=ICON_CHOICES, default="book")
    image = models.ImageField(_("Rasm"), upload_to="courses/", blank=True, validators=image_validators)
    is_featured = models.BooleanField(_("Top kurs (qizil belgi)"), default=False)

    meta_title = models.CharField(_("SEO sarlavha"), max_length=200, blank=True)
    meta_description = models.TextField(_("SEO tavsif"), blank=True)
    og_image = models.ImageField(_("OG rasm"), upload_to="courses/og/", blank=True,
                                 validators=image_validators)

    class Meta(OrderedActiveModel.Meta):
        verbose_name = _("Kurs")
        verbose_name_plural = _("Kurslar")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("courses:detail", kwargs={"slug": self.slug})


class CourseImage(OrderedActiveModel):
    """Extra images shown in a gallery on the course detail page."""

    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="images",
        verbose_name=_("Kurs"),
    )
    image = models.ImageField(_("Rasm"), upload_to="courses/gallery/",
                              validators=image_validators)
    caption = models.CharField(_("Izoh"), max_length=200, blank=True)

    class Meta(OrderedActiveModel.Meta):
        verbose_name = _("Kurs rasmi")
        verbose_name_plural = _("Kurs rasmlari")

    def __str__(self):
        return self.caption or f"Rasm #{self.pk}"
