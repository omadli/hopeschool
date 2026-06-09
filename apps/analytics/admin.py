from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import VisitLog


@admin.register(VisitLog)
class VisitLogAdmin(ModelAdmin):
    list_display = (
        "created_at",
        "path",
        "device_type",
        "browser",
        "os",
        "country",
        "ip_address",
        "language",
    )
    list_filter = ("device_type", "country", "created_at", "language")
    search_fields = ("path", "ip_address", "country")
    date_hierarchy = "created_at"
    readonly_fields = (
        "path",
        "method",
        "referrer",
        "ip_address",
        "country",
        "country_code",
        "user_agent",
        "device_type",
        "browser",
        "os",
        "language",
        "created_at",
    )

    def has_add_permission(self, request):
        # Visits are written only by the middleware; never created by hand.
        return False
