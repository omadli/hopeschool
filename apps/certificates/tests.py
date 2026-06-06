"""Tests for apps.certificates — models, views, admin."""
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.certificates.models import Certificate

User = get_user_model()

_STATIC_STORAGE = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
    },
}


class CertificateModelTests(TestCase):
    """Certificate model — __str__, clean(), link property."""

    def _make(self, **kwargs):
        defaults = {"title": "Test sertifikat", "is_active": True}
        defaults.update(kwargs)
        c = Certificate(**defaults)
        return c

    def test_str(self):
        c = self._make(external_url="https://example.com")
        c.save()
        self.assertEqual(str(c), "Test sertifikat")

    def test_clean_raises_when_no_file_or_url(self):
        c = self._make()  # no image, no pdf_file, no external_url
        with self.assertRaises(ValidationError):
            c.clean()

    def test_clean_passes_with_external_url(self):
        c = self._make(external_url="https://example.com/cert")
        # Should not raise
        c.clean()

    def test_clean_passes_with_image(self):
        c = self._make()
        c.image = "certificates/test.jpg"  # set a path (no actual upload needed for clean())
        # Should not raise
        c.clean()

    def test_link_prefers_external_url(self):
        c = self._make(external_url="https://example.com/cert")
        c.image = "certificates/test.jpg"
        c.save()
        self.assertEqual(c.link, "https://example.com/cert")

    def test_link_falls_back_to_image(self):
        c = self._make()
        c.image = "certificates/test.jpg"
        c.save()
        # link should return image url
        self.assertIn("certificates/test.jpg", c.link)

    def test_link_empty_when_nothing_set(self):
        c = self._make()
        c.save()
        self.assertEqual(c.link, "")

    def test_i18n_fields_exist(self):
        c = Certificate()
        self.assertTrue(hasattr(c, "title_uz"))
        self.assertTrue(hasattr(c, "title_ru"))
        self.assertTrue(hasattr(c, "title_en"))


@override_settings(STORAGES=_STATIC_STORAGE)
class CertificateListViewTests(TestCase):
    """Certificate list view returns 200."""

    def setUp(self):
        Certificate.objects.create(
            title="IELTS 7.5",
            is_active=True,
            external_url="https://example.com/cert1",
        )

    def test_list_view_200(self):
        url = reverse("certificates:list")
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)


@override_settings(STORAGES=_STATIC_STORAGE)
class CertificateAdminTests(TestCase):
    """Admin changelist and add pages return 200 for certificates."""

    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="admin_certs",
            password="adminpass123",
            email="admin_certs@test.com",
        )
        self.client.force_login(self.superuser)

    def _get(self, url):
        return self.client.get(url, follow=True)

    def test_certificate_changelist(self):
        url = reverse("admin:certificates_certificate_changelist")
        self.assertEqual(self._get(url).status_code, 200)

    def test_certificate_add(self):
        url = reverse("admin:certificates_certificate_add")
        self.assertEqual(self._get(url).status_code, 200)
