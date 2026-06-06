"""Tests for apps.pages — i18n URL redirects, landing view, admin pages."""
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.pages.models import AboutSection

User = get_user_model()

_STATIC_STORAGE = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
    },
}


@override_settings(STORAGES=_STATIC_STORAGE)
class I18nRedirectTests(TestCase):
    """Root URL / → 302 to /uz/; language prefixed URLs → 200."""

    def test_root_redirects(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/uz/", response["Location"])

    def test_uz_home_ok(self):
        response = self.client.get("/uz/", follow=True)
        self.assertEqual(response.status_code, 200)

    def test_ru_home_ok(self):
        response = self.client.get("/ru/", follow=True)
        self.assertEqual(response.status_code, 200)

    def test_en_home_ok(self):
        response = self.client.get("/en/", follow=True)
        self.assertEqual(response.status_code, 200)


class AboutSectionModelTests(TestCase):
    """AboutSection model basics."""

    def test_str(self):
        section = AboutSection.objects.create(
            title="Biz haqimizda",
            is_active=True,
        )
        self.assertEqual(str(section), "Biz haqimizda")

    def test_i18n_fields_exist(self):
        """modeltranslation creates _uz / _ru / _en variants."""
        section = AboutSection()
        self.assertTrue(hasattr(section, "title_uz"))
        self.assertTrue(hasattr(section, "title_ru"))
        self.assertTrue(hasattr(section, "title_en"))


@override_settings(STORAGES=_STATIC_STORAGE)
class PagesAdminTests(TestCase):
    """Admin changelist and add pages return 200 for pages app models."""

    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="admin_pages",
            password="adminpass123",
            email="admin_pages@test.com",
        )
        self.client.force_login(self.superuser)

    def _get(self, url):
        return self.client.get(url, follow=True)

    def test_aboutsection_changelist(self):
        url = reverse("admin:pages_aboutsection_changelist")
        self.assertEqual(self._get(url).status_code, 200)

    def test_aboutsection_add(self):
        url = reverse("admin:pages_aboutsection_add")
        self.assertEqual(self._get(url).status_code, 200)

    def test_statitem_changelist(self):
        url = reverse("admin:pages_statitem_changelist")
        self.assertEqual(self._get(url).status_code, 200)

    def test_whyusitem_changelist(self):
        url = reverse("admin:pages_whyusitem_changelist")
        self.assertEqual(self._get(url).status_code, 200)
