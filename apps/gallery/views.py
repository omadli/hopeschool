from django.views.generic import TemplateView

from .models import GalleryAlbum, GalleryImage, GalleryVideo


class GalleryListView(TemplateView):
    template_name = "gallery/list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["albums"] = (
            GalleryAlbum.objects.filter(is_active=True)
            .prefetch_related("images")
        )
        ctx["images"] = GalleryImage.objects.filter(is_active=True).select_related("album")
        ctx["videos"] = GalleryVideo.objects.filter(is_active=True).select_related("album")
        return ctx
