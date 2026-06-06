from modeltranslation.translator import TranslationOptions, register

from .models import GalleryAlbum


@register(GalleryAlbum)
class GalleryAlbumTR(TranslationOptions):
    fields = ("title", "description")
