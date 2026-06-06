from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _

MAX_IMAGE_MB = 5
MAX_DOC_MB = 10


@deconstructible
class MaxFileSizeValidator:
    """Reusable, migration-serializable max upload size validator."""

    def __init__(self, max_mb):
        self.max_mb = max_mb

    def __call__(self, file):
        size = getattr(file, "size", None)
        if size and size > self.max_mb * 1024 * 1024:
            raise ValidationError(
                _("Fayl hajmi %(mb)s MB dan oshmasligi kerak.") % {"mb": self.max_mb}
            )

    def __eq__(self, other):
        return isinstance(other, MaxFileSizeValidator) and self.max_mb == other.max_mb


image_validators = [
    FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "webp", "gif"]),
    MaxFileSizeValidator(MAX_IMAGE_MB),
]

pdf_validators = [
    FileExtensionValidator(allowed_extensions=["pdf"]),
    MaxFileSizeValidator(MAX_DOC_MB),
]
