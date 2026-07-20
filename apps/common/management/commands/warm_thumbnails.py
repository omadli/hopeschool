"""Pre-generate image thumbnails by rendering the image-heavy public pages once.

easy-thumbnails builds each variant lazily on first request, so without this the
FIRST visitor after a deploy (or after new content is uploaded) pays the full
Pillow resize + WebP encode for every image on the page — enough to tie up a
gunicorn worker and 502. Run this at the end of the deploy so that cost is paid
by the deploy, not a real user.

Renders through the actual views with RequestFactory (no network, no server), so
it exercises the exact {% responsive_img %} calls the templates use.
"""
from django.conf import settings
from django.core.management.base import BaseCommand
from django.test import RequestFactory
from django.urls import reverse

from apps.gallery.views import GalleryListView
from apps.pages.views import LandingView


class Command(BaseCommand):
    help = "Render the landing + gallery once to pre-generate thumbnails."

    def handle(self, *args, **options):
        host = next((h for h in settings.ALLOWED_HOSTS if h not in ("*", "")), "localhost")
        rf = RequestFactory()
        targets = [
            ("landing", "/", LandingView),
            ("gallery", reverse("gallery:list"), GalleryListView),
        ]
        for label, path, view in targets:
            try:
                request = rf.get(path, HTTP_HOST=host, secure=True)
                view.as_view()(request).render()
                self.stdout.write(self.style.SUCCESS(f"warmed: {label}"))
            except Exception as exc:  # deploy convenience — never fail the deploy
                self.stderr.write(f"skip {label}: {exc}")
