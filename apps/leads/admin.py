from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from .models import Lead, LeadSource


@admin.register(LeadSource)
class LeadSourceAdmin(ModelAdmin):
    list_display = ("name", "slug", "lead_count", "is_active", "order")
    list_editable = ("is_active", "order")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    fields = ("name", "slug", "icon", "image", "color", "is_active", "order")

    @admin.display(description=_("Lidlar"))
    def lead_count(self, obj):
        return obj.leads.count()

    def get_readonly_fields(self, request, obj=None):
        # Built-in channels keep their slug (ad links depend on it).
        if obj and obj.is_protected:
            return ("slug",)
        return ()

    def get_prepopulated_fields(self, request, obj=None):
        if obj and obj.is_protected:
            return {}
        return self.prepopulated_fields

    def has_delete_permission(self, request, obj=None):
        if obj and obj.is_protected:
            return False
        return super().has_delete_permission(request, obj)


@admin.register(Lead)
class LeadAdmin(ModelAdmin):
    list_display = ("full_name", "phone", "course", "source", "status", "is_notified", "created_at")
    list_editable = ("status",)
    list_filter = ("status", "source", "course", "created_at")
    search_fields = ("full_name", "phone")
    date_hierarchy = "created_at"
    autocomplete_fields = ("source",)
    readonly_fields = ("referrer", "is_notified", "created_at", "updated_at")
    list_per_page = 50
    fieldsets = (
        (None, {"fields": ("full_name", "phone", "course", "message", "status", "source")}),
        (None, {"fields": ("referrer", "is_notified", "created_at", "updated_at"),
                "classes": ("collapse",)}),
    )
