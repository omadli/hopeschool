from modeltranslation.translator import TranslationOptions, register

from .models import (
    AboutSection,
    HeroSection,
    HomeVideo,
    Partner,
    SiteCopy,
    StatItem,
    WhyUsItem,
)


@register(AboutSection)
class AboutSectionTR(TranslationOptions):
    fields = ("title", "subtitle", "body")


@register(StatItem)
class StatItemTR(TranslationOptions):
    fields = ("label",)


@register(WhyUsItem)
class WhyUsItemTR(TranslationOptions):
    fields = ("title", "description")


@register(Partner)
class PartnerTR(TranslationOptions):
    fields = ("name",)


# NOTE: these singletons set a model `default=` on their translatable fields.
# By default modeltranslation treats a value EQUAL to that default as
# "undefined" and falls back to another language — so the UZ page would render
# RU. `fallback_undefined = ""` makes only an empty string trigger fallback, so
# real UZ content (even when it matches the default) is shown as-is.
@register(HeroSection)
class HeroSectionTR(TranslationOptions):
    fields = ("badge_text", "title_prefix", "title_suffix",
              "primary_cta", "secondary_cta")
    fallback_undefined = ""


@register(SiteCopy)
class SiteCopyTR(TranslationOptions):
    fields = ("results_eyebrow", "results_title", "results_link_label",
              "testimonials_title", "contact_eyebrow", "contact_title",
              "contact_intro", "lead_submit_label", "modal_title",
              "modal_subtitle", "modal_submit_label", "footer_note")
    fallback_undefined = ""


@register(HomeVideo)
class HomeVideoTR(TranslationOptions):
    fields = ("title", "subtitle")
