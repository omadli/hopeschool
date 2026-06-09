from django.contrib import admin
from modeltranslation.admin import TabbedTranslationAdmin
from unfold.admin import ModelAdmin, TabularInline

from apps.common.admin import AutoTranslateAdminMixin

from .models import GalleryAlbum, GalleryImage, GalleryVideo


class GalleryImageInline(TabularInline):
    model = GalleryImage
    extra = 1
    fields = ("image", "caption", "alt_text", "order", "is_active")
    ordering = ("order",)


class GalleryVideoInline(TabularInline):
    model = GalleryVideo
    extra = 0
    fields = ("video_url", "video_file", "title", "thumbnail", "order", "is_active")
    ordering = ("order",)


@admin.register(GalleryAlbum)
class GalleryAlbumAdmin(AutoTranslateAdminMixin, ModelAdmin, TabbedTranslationAdmin):
    list_display = ("title", "is_active", "order")
    list_editable = ("is_active", "order")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [GalleryImageInline, GalleryVideoInline]


@admin.register(GalleryVideo)
class GalleryVideoAdmin(AutoTranslateAdminMixin, ModelAdmin, TabbedTranslationAdmin):
    list_display = ("__str__", "album", "is_active", "order")
    list_editable = ("is_active", "order")
    list_filter = ("album", "is_active")


@admin.register(GalleryImage)
class GalleryImageAdmin(ModelAdmin):
    list_display = ("__str__", "album", "is_active", "order")
    list_editable = ("is_active", "order")
    list_filter = ("album", "is_active")
