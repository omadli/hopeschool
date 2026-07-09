from django import forms
from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _
from modeltranslation.admin import TabbedTranslationAdmin
from unfold.admin import ModelAdmin

from apps.common.admin import AutoTranslateAdminMixin

from .models import Certificate
from .services import CertificateImportError, populate_certificate
from .widgets import QRURLWidget


class CertificateAdminForm(forms.ModelForm):
    class Meta:
        model = Certificate
        fields = "__all__"
        widgets = {"external_url": QRURLWidget()}


@admin.register(Certificate)
class CertificateAdmin(AutoTranslateAdminMixin, ModelAdmin, TabbedTranslationAdmin):
    form = CertificateAdminForm
    list_display = ("title", "student_name", "badge", "issued_on", "is_active", "order")
    list_editable = ("is_active", "order")
    list_filter = ("badge", "is_active")
    ordering = ("-issued_on",)
    search_fields = ("title", "student_name")
    actions = ["import_selected_from_url"]
    fieldsets = (
        (None, {"fields": ("title", "student_name", "description", "badge", "badge_accent")}),
        (_("CEFR / havola (QR skaner)"), {
            "fields": ("external_url", "image", "pdf_file", "issued_on"),
            "description": _("CEFR sertifikati havolasini kiriting yoki QR kodni skanerlang — saqlaganda PDF rasmga aylantiriladi va oʻquvchi ismi aniqlanadi."),
        }),
        (_("Holat"), {"fields": ("is_active", "order")}),
    )

    def save_model(self, request, obj, form, change):
        # QR-scan / paste a URL, then save → fetch PDF, render image, parse name.
        # Only when there's a URL and no image yet (re-import via the action).
        if obj.external_url and not obj.image:
            try:
                populate_certificate(obj, save=False)
                messages.success(
                    request,
                    _("Havoladan import qilindi (rasm + ism aniqlandi). Tekshirib saqlang."),
                )
            except CertificateImportError as exc:
                messages.warning(
                    request, _("Avto-import boʻlmadi: %(e)s") % {"e": exc}
                )
        super().save_model(request, obj, form, change)

    @admin.action(description=_("Havoladan qayta import qilish (PDF→rasm + ism)"))
    def import_selected_from_url(self, request, queryset):
        ok = failed = 0
        for cert in queryset:
            if not cert.external_url:
                continue
            try:
                populate_certificate(cert, save=True)
                ok += 1
            except CertificateImportError:
                failed += 1
        self.message_user(
            request,
            _("Import yakunlandi — muvaffaqiyatli: %(ok)d, xato: %(f)d.")
            % {"ok": ok, "f": failed},
            level=messages.SUCCESS if not failed else messages.WARNING,
        )
