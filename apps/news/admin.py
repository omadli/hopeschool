from django.contrib import admin
from modeltranslation.admin import TabbedTranslationAdmin
from unfold.admin import ModelAdmin

from apps.common.admin import AutoTranslateAdminMixin

from .models import NewsPost


@admin.register(NewsPost)
class NewsPostAdmin(AutoTranslateAdminMixin, ModelAdmin, TabbedTranslationAdmin):
    list_display = ("title", "badge", "published_at", "is_published", "is_featured")
    list_editable = ("is_published", "is_featured")
    list_filter = ("is_published", "is_featured", "badge")
    search_fields = ("title", "excerpt", "body")
    date_hierarchy = "published_at"
    prepopulated_fields = {"slug": ("title",)}
    fieldsets = (
        (None, {"fields": ("title", "slug", "excerpt", "body", "cover_image")}),
        ("Video", {"fields": ("video_url", "video_file")}),
        ("Belgi", {"fields": ("badge", "badge_accent")}),
        ("Holat", {"fields": ("published_at", "is_published", "is_featured")}),
        ("SEO", {"fields": ("meta_title", "meta_description"), "classes": ("collapse",)}),
    )
