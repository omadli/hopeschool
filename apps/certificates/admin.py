from django.contrib import admin
from modeltranslation.admin import TabbedTranslationAdmin
from unfold.admin import ModelAdmin

from .models import Certificate


@admin.register(Certificate)
class CertificateAdmin(ModelAdmin, TabbedTranslationAdmin):
    list_display = ("title", "student_name", "badge", "is_active", "order")
    list_editable = ("is_active", "order")
    list_filter = ("badge", "is_active")
    search_fields = ("title", "student_name")
    fieldsets = (
        (None, {"fields": ("title", "student_name", "description", "badge", "badge_accent")}),
        ("Fayl (kamida bittasi)", {"fields": ("image", "pdf_file", "external_url")}),
        ("Holat", {"fields": ("is_active", "order")}),
    )
