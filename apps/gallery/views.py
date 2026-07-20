from django.core.paginator import Paginator
from django.views.generic import TemplateView

from .models import GalleryImage, GalleryVideo


class GalleryListView(TemplateView):
    template_name = "gallery/list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        images = GalleryImage.objects.filter(is_active=True).select_related("album")
        page = Paginator(images, 24).get_page(self.request.GET.get("page"))
        ctx["images"] = page
        # Videos are usually few — show them once, on the first page only.
        if page.number == 1:
            ctx["videos"] = GalleryVideo.objects.filter(is_active=True).select_related("album")
        return ctx
