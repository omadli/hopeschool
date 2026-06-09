from django import forms


class QRURLWidget(forms.URLInput):
    """URL input with a camera QR-scanner button.

    Scanning a CEFR certificate's QR code fills this field with the verification
    URL; on save the admin auto-imports the PDF (render + name). The scanner JS
    needs HTTPS or localhost (browser camera requirement).
    """

    def __init__(self, attrs=None):
        attrs = {**(attrs or {}), "data-qr-scan": "1",
                 "placeholder": "https://app.uzbmb.uz/cefr/certificates/….pdf"}
        super().__init__(attrs)

    class Media:
        js = ("js/vendor/jsQR.min.js", "js/admin_qr_scanner.js")
