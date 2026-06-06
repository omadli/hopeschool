from django.contrib import admin
from modeltranslation.admin import TabbedTranslationAdmin
from unfold.admin import ModelAdmin

from .models import AboutSection, StatItem, WhyUsItem


@admin.register(AboutSection)
class AboutSectionAdmin(ModelAdmin, TabbedTranslationAdmin):
    list_display = ("title", "is_active", "order")
    list_editable = ("is_active", "order")


@admin.register(StatItem)
class StatItemAdmin(ModelAdmin, TabbedTranslationAdmin):
    list_display = ("label", "number", "suffix", "accent", "is_active", "order")
    list_editable = ("number", "suffix", "accent", "is_active", "order")


@admin.register(WhyUsItem)
class WhyUsItemAdmin(ModelAdmin, TabbedTranslationAdmin):
    list_display = ("title", "icon", "accent", "is_active", "order")
    list_editable = ("icon", "accent", "is_active", "order")
