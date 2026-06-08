from modeltranslation.translator import TranslationOptions, register

from .models import AboutSection, HeroSection, SiteCopy, StatItem, WhyUsItem


@register(AboutSection)
class AboutSectionTR(TranslationOptions):
    fields = ("title", "subtitle", "body")


@register(StatItem)
class StatItemTR(TranslationOptions):
    fields = ("label",)


@register(WhyUsItem)
class WhyUsItemTR(TranslationOptions):
    fields = ("title", "description")


@register(HeroSection)
class HeroSectionTR(TranslationOptions):
    fields = ("badge_text", "title_prefix", "title_suffix",
              "primary_cta", "secondary_cta")


@register(SiteCopy)
class SiteCopyTR(TranslationOptions):
    fields = ("results_eyebrow", "results_title", "results_link_label",
              "testimonials_title", "contact_eyebrow", "contact_title",
              "contact_intro", "lead_submit_label", "modal_title",
              "modal_subtitle", "modal_submit_label", "footer_note")
