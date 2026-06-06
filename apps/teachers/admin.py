from django.contrib import admin
from modeltranslation.admin import TabbedTranslationAdmin
from unfold.admin import ModelAdmin

from .models import Teacher


@admin.register(Teacher)
class TeacherAdmin(ModelAdmin, TabbedTranslationAdmin):
    list_display = ("full_name", "position", "experience_years", "is_active", "order")
    list_editable = ("is_active", "order")
    list_filter = ("is_active",)
    search_fields = ("full_name", "position", "subjects")
    prepopulated_fields = {"slug": ("full_name",)}
    fieldsets = (
        (None, {"fields": ("full_name", "slug", "photo", "position", "subjects", "experience_years", "bio")}),
        ("Ijtimoiy tarmoqlar", {"fields": ("instagram_url", "telegram_url", "youtube_url")}),
        ("Holat", {"fields": ("is_active", "order")}),
        ("SEO", {"fields": ("meta_title", "meta_description"), "classes": ("collapse",)}),
    )
