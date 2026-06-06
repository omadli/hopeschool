from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Lead


@admin.register(Lead)
class LeadAdmin(ModelAdmin):
    list_display = ("full_name", "phone", "course", "status", "is_notified", "created_at")
    list_editable = ("status",)
    list_filter = ("status", "course", "created_at")
    search_fields = ("full_name", "phone")
    date_hierarchy = "created_at"
    readonly_fields = ("source", "is_notified", "created_at", "updated_at")
    list_per_page = 50
    fieldsets = (
        (None, {"fields": ("full_name", "phone", "course", "message", "status")}),
        (None, {"fields": ("source", "is_notified", "created_at", "updated_at"),
                "classes": ("collapse",)}),
    )
