from modeltranslation.translator import TranslationOptions, register

from .models import GalleryAlbum, GalleryImage


@register(GalleryAlbum)
class GalleryAlbumTR(TranslationOptions):
    fields = ("title", "description")


@register(GalleryImage)
class GalleryImageTR(TranslationOptions):
    # caption + alt_text are user-facing (rendered as <img alt> on the site),
    # so they must be editable in all 3 languages.
    # NOTE: requires `makemigrations gallery` + `migrate` (adds caption_uz/ru/en,
    # alt_text_uz/ru/en). The orchestrator must run the migration.
    fields = ("caption", "alt_text")
