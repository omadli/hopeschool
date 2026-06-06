"""Tests for apps.testimonials — models, admin."""
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.testimonials.models import Testimonial

User = get_user_model()

_STATIC_STORAGE = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
    },
}


class TestimonialModelTests(TestCase):
    """Testimonial model basics."""

    def setUp(self):
        self.testimonial = Testimonial.objects.create(
            author_name="Dilnoza Yusupova",
            content="Juda yaxshi kurs!",
            is_active=True,
        )

    def test_str(self):
        self.assertEqual(str(self.testimonial), "Dilnoza Yusupova")

    def test_i18n_fields_exist(self):
        """modeltranslation creates translated field variants."""
        t = Testimonial()
        self.assertTrue(hasattr(t, "content_uz"))
        self.assertTrue(hasattr(t, "content_ru"))
        self.assertTrue(hasattr(t, "content_en"))


@override_settings(STORAGES=_STATIC_STORAGE)
class TestimonialAdminTests(TestCase):
    """Admin changelist and add pages return 200 for testimonials."""

    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="admin_testimonials",
            password="adminpass123",
            email="admin_testimonials@test.com",
        )
        self.client.force_login(self.superuser)

    def _get(self, url):
        return self.client.get(url, follow=True)

    def test_testimonial_changelist(self):
        url = reverse("admin:testimonials_testimonial_changelist")
        self.assertEqual(self._get(url).status_code, 200)

    def test_testimonial_add(self):
        url = reverse("admin:testimonials_testimonial_add")
        self.assertEqual(self._get(url).status_code, 200)
