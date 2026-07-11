from modeltranslation.translator import TranslationOptions, register

from .models import Certificate


@register(Certificate)
class CertificateTR(TranslationOptions):
    # badge (IELTS 7, B2, SAT...) reads identically in every language — not
    # translated, unlike title/description.
    fields = ("title", "description")
