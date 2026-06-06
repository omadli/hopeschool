from django import forms
from django.utils.translation import gettext_lazy as _

from apps.common.utils import normalize_phone

from .models import Lead


class LeadForm(forms.ModelForm):
    """Public application form with a hidden honeypot anti-spam field."""

    # Honeypot: real users never see/fill this. Bots that fill every field do.
    website = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = Lead
        fields = ("full_name", "phone", "course", "message")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["full_name"].required = True
        self.fields["phone"].required = True

    def clean_website(self):
        """If the honeypot is filled, mark the submission as spam."""
        if self.cleaned_data.get("website"):
            raise forms.ValidationError("spam")
        return ""

    def clean_phone(self):
        phone = normalize_phone(self.cleaned_data.get("phone"))
        digits = "".join(ch for ch in (phone or "") if ch.isdigit())
        if not (phone.startswith("+998") and len(digits) == 12):
            raise forms.ValidationError(
                _("Telefon raqamni +998XXXXXXXXX koʻrinishida kiriting.")
            )
        return phone
