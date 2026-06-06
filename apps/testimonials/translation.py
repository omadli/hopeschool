from modeltranslation.translator import TranslationOptions, register

from .models import Testimonial


@register(Testimonial)
class TestimonialTR(TranslationOptions):
    fields = ("author_role", "content")
