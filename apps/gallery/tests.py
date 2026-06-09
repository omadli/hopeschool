"""Tests for apps.gallery — models, views, admin."""
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.gallery.models import GalleryAlbum, GalleryImage

User = get_user_model()

_STATIC_STORAGE = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
    },
}


class GalleryModelTests(TestCase):
    """GalleryAlbum and GalleryImage model basics."""

    def setUp(self):
        self.album = GalleryAlbum.objects.create(
            title="Sinfxona",
            slug="sinfxona",
            is_active=True,
        )

    def test_album_str(self):
        self.assertEqual(str(self.album), "Sinfxona")

    def test_album_i18n_fields(self):
        self.assertTrue(hasattr(self.album, "title_uz"))
        self.assertTrue(hasattr(self.album, "title_ru"))
        self.assertTrue(hasattr(self.album, "title_en"))

    def test_gallery_image_str_with_caption(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        # Create image inline — we just need the str, so use a minimal file path trick
        img = GalleryImage(
            album=self.album,
            caption="Birinchi rasm",
            is_active=True,
        )
        img.image = "gallery/test.jpg"  # avoid file upload
        img.save()
        self.assertEqual(str(img), "Birinchi rasm")

    def test_gallery_image_str_no_caption(self):
        img = GalleryImage(album=self.album, is_active=True)
        img.image = "gallery/test2.jpg"
        img.save()
        # str should contain "Rasm #" + pk
        self.assertIn("Rasm #", str(img))


@override_settings(STORAGES=_STATIC_STORAGE)
class GalleryListViewTests(TestCase):
    """Gallery list view returns 200."""

    def setUp(self):
        self.album = GalleryAlbum.objects.create(
            title="Galereya",
            slug="galereya",
            is_active=True,
        )

    def test_list_view_200(self):
        url = reverse("gallery:list")
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)


@override_settings(STORAGES=_STATIC_STORAGE)
class GalleryAdminTests(TestCase):
    """Admin changelist and add pages return 200 for gallery."""

    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="admin_gallery",
            password="adminpass123",
            email="admin_gallery@test.com",
        )
        self.client.force_login(self.superuser)

    def _get(self, url):
        return self.client.get(url, follow=True)

    def test_galleryalbum_changelist(self):
        url = reverse("admin:gallery_galleryalbum_changelist")
        self.assertEqual(self._get(url).status_code, 200)

    def test_galleryalbum_add(self):
        url = reverse("admin:gallery_galleryalbum_add")
        self.assertEqual(self._get(url).status_code, 200)


# ---------------------------------------------------------------------------
# Phase E — gallery video
# ---------------------------------------------------------------------------
@override_settings(STORAGES=_STATIC_STORAGE)
class GalleryVideoTests(TestCase):
    def test_video_renders_on_list(self):
        from apps.gallery.models import GalleryVideo
        GalleryVideo.objects.create(
            title="Tadbir", video_url="https://youtu.be/dQw4w9WgXcQ", is_active=True)
        body = self.client.get(reverse("gallery:list"), follow=True).content.decode(
            "utf-8", "replace")
        self.assertIn("youtube.com/embed/dQw4w9WgXcQ", body)

    def test_galleryvideo_admin_changelist(self):
        from django.contrib.auth import get_user_model
        admin = get_user_model().objects.create_superuser(
            username="admin_gv", password="pw12345678", email="gv@test.com")
        self.client.force_login(admin)
        url = reverse("admin:gallery_galleryvideo_changelist")
        self.assertEqual(self.client.get(url, follow=True).status_code, 200)
