from modeltranslation.translator import TranslationOptions, register

from .models import Certificate


@register(Certificate)
class CertificateTR(TranslationOptions):
    fields = ("title", "description", "badge")
