from django import forms
from django.utils.translation import gettext_lazy as _


class QRURLWidget(forms.URLInput):
    """URL input with a camera QR-scanner button.

    Scanning a CEFR certificate's QR code fills this field with the verification
    URL; on save the admin auto-imports the PDF (render + name). The scanner JS
    needs HTTPS or localhost (browser camera requirement).

    The scanner's user-facing strings are passed as ``data-*`` attributes so
    admin_qr_scanner.js can show them in the active admin language (the JS has
    no gettext catalog of its own).
    """

    def __init__(self, attrs=None):
        attrs = {
            **(attrs or {}),
            "data-qr-scan": "1",
            "placeholder": "https://app.uzbmb.uz/cefr/certificates/….pdf",
            "data-qr-label": _("📷 QR kodni skanerlash"),
            "data-qr-close": _("Yopish"),
            "data-qr-found": _("Topildi:"),
            "data-qr-opening": _("Kamera ochilmoqda…"),
            "data-qr-aim": _("QR kodni kameraga toʻgʻrilang…"),
            "data-qr-denied": _("Kameraga ruxsat berilmadi:"),
            "data-qr-nocam": _("Bu brauzerda kamera ishlamaydi. Havolani qoʻlda kiriting."),
        }
        super().__init__(attrs)

    class Media:
        js = ("js/vendor/jsQR.min.js", "js/admin_qr_scanner.js")
