from django.contrib import admin
from modeltranslation.admin import TabbedTranslationAdmin
from unfold.admin import ModelAdmin

from apps.common.admin import AutoTranslateAdminMixin

from .models import Course, CourseCategory


@admin.register(CourseCategory)
class CourseCategoryAdmin(AutoTranslateAdminMixin, ModelAdmin, TabbedTranslationAdmin):
    list_display = ("name", "is_active", "order")
    list_editable = ("is_active", "order")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Course)
class CourseAdmin(AutoTranslateAdminMixin, ModelAdmin, TabbedTranslationAdmin):
    list_display = ("name", "category", "price", "is_featured", "is_active", "order")
    list_editable = ("is_featured", "is_active", "order")
    list_filter = ("category", "is_featured", "is_active")
    search_fields = ("name", "short_description")
    prepopulated_fields = {"slug": ("name",)}
    fieldsets = (
        (None, {"fields": ("category", "name", "slug", "short_description", "description")}),
        ("Tafsilotlar", {"fields": ("duration_text", "group_size", "icon", "image", "is_featured")}),
        ("Narx", {"fields": ("price", "price_note", "is_price_visible")}),
        ("Holat", {"fields": ("is_active", "order")}),
        ("SEO", {"fields": ("meta_title", "meta_description", "og_image"), "classes": ("collapse",)}),
    )
