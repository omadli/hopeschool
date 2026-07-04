from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from modeltranslation.admin import TabbedTranslationAdmin
from solo.admin import SingletonModelAdmin
from unfold.admin import ModelAdmin

from apps.common.admin import AutoTranslateAdminMixin

from .models import (
    AboutSection,
    HeroSection,
    HomeVideo,
    SiteCopy,
    StatItem,
    WhyUsItem,
)


@admin.register(AboutSection)
class AboutSectionAdmin(AutoTranslateAdminMixin, ModelAdmin, TabbedTranslationAdmin):
    list_display = ("title", "is_active", "order")
    list_editable = ("is_active", "order")


@admin.register(StatItem)
class StatItemAdmin(AutoTranslateAdminMixin, ModelAdmin, TabbedTranslationAdmin):
    list_display = ("label", "number", "suffix", "accent", "is_active", "order")
    list_editable = ("number", "suffix", "accent", "is_active", "order")


@admin.register(WhyUsItem)
class WhyUsItemAdmin(AutoTranslateAdminMixin, ModelAdmin, TabbedTranslationAdmin):
    list_display = ("title", "icon", "accent", "is_active", "order")
    list_editable = ("icon", "accent", "is_active", "order")


@admin.register(HeroSection)
class HeroSectionAdmin(AutoTranslateAdminMixin, ModelAdmin, TabbedTranslationAdmin, SingletonModelAdmin):
    fieldsets = (
        (_("Yorliq va sarlavha"), {
            "fields": ("badge_text", "title_prefix", "title_suffix"),
            "description": _("To'liq sarlavha: «Sarlavha boshi» + sayt nomi + «Sarlavha oxiri»."),
        }),
        (_("Tugmalar"), {
            "fields": ("primary_cta", "secondary_cta"),
        }),
        (_("Suzuvchi yorliqlar"), {
            "fields": ("metric1_value", "metric2_value"),
            "description": _("Hero rasmi ustidagi kichik kartalardagi raqamlar."),
        }),
    )


@admin.register(HomeVideo)
class HomeVideoAdmin(AutoTranslateAdminMixin, ModelAdmin, TabbedTranslationAdmin, SingletonModelAdmin):
    fieldsets = (
        (_("Holat"), {"fields": ("is_enabled",)}),
        (_("Matn"), {"fields": ("title", "subtitle")}),
        (_("Video"), {
            "fields": ("video_url", "video_file"),
            "description": _("YouTube/Vimeo havola yoki video fayl yuklang."),
        }),
    )


@admin.register(SiteCopy)
class SiteCopyAdmin(AutoTranslateAdminMixin, ModelAdmin, TabbedTranslationAdmin, SingletonModelAdmin):
    fieldsets = (
        (_("Natijalar bo'limi"), {
            "fields": ("results_eyebrow", "results_title",
                       "results_link_label", "testimonials_title"),
        }),
        (_("Kontakt bo'limi"), {
            "fields": ("contact_eyebrow", "contact_title",
                       "contact_intro", "lead_submit_label"),
        }),
        (_("Ariza oynasi (modal)"), {
            "fields": ("modal_title", "modal_subtitle", "modal_submit_label"),
        }),
        (_("Footer"), {
            "fields": ("footer_note",),
        }),
    )
