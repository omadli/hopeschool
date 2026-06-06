from modeltranslation.translator import TranslationOptions, register

from .models import AboutSection, StatItem, WhyUsItem


@register(AboutSection)
class AboutSectionTR(TranslationOptions):
    fields = ("title", "subtitle", "body")


@register(StatItem)
class StatItemTR(TranslationOptions):
    fields = ("label",)


@register(WhyUsItem)
class WhyUsItemTR(TranslationOptions):
    fields = ("title", "description")
