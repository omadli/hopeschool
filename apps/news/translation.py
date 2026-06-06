from modeltranslation.translator import TranslationOptions, register

from .models import NewsPost


@register(NewsPost)
class NewsPostTR(TranslationOptions):
    fields = ("title", "excerpt", "body", "badge", "meta_title", "meta_description")
