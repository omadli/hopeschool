"""Tests for apps.teachers — models, views, admin."""
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.teachers.models import Teacher

User = get_user_model()

_STATIC_STORAGE = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
    },
}


class TeacherModelTests(TestCase):
    """Teacher model basics."""

    def setUp(self):
        self.teacher = Teacher.objects.create(
            full_name="Aziz Karimov",
            slug="aziz-karimov",
            position="Python o'qituvchisi",
            is_active=True,
        )

    def test_str(self):
        self.assertEqual(str(self.teacher), "Aziz Karimov")

    def test_get_absolute_url(self):
        url = self.teacher.get_absolute_url()
        self.assertIn("aziz-karimov", url)
        self.assertIn("oqituvchilar", url)

    def test_i18n_fields_exist(self):
        """modeltranslation creates _uz / _ru / _en variants for translated fields."""
        self.assertTrue(hasattr(self.teacher, "position_uz"))
        self.assertTrue(hasattr(self.teacher, "position_ru"))
        self.assertTrue(hasattr(self.teacher, "position_en"))


@override_settings(STORAGES=_STATIC_STORAGE)
class TeacherDetailViewTests(TestCase):
    """Teacher detail view returns 200."""

    def setUp(self):
        self.teacher = Teacher.objects.create(
            full_name="Test Teacher",
            slug="test-teacher",
            is_active=True,
        )

    def test_detail_view_200(self):
        url = self.teacher.get_absolute_url()
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_inactive_teacher_404(self):
        inactive = Teacher.objects.create(
            full_name="Yashirin Teacher",
            slug="yashirin-teacher",
            is_active=False,
        )
        url = inactive.get_absolute_url()
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 404)


@override_settings(STORAGES=_STATIC_STORAGE)
class TeacherAdminTests(TestCase):
    """Admin changelist and add pages return 200 for teachers."""

    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="admin_teachers",
            password="adminpass123",
            email="admin_teachers@test.com",
        )
        self.client.force_login(self.superuser)

    def _get(self, url):
        return self.client.get(url, follow=True)

    def test_teacher_changelist(self):
        url = reverse("admin:teachers_teacher_changelist")
        self.assertEqual(self._get(url).status_code, 200)

    def test_teacher_add(self):
        url = reverse("admin:teachers_teacher_add")
        self.assertEqual(self._get(url).status_code, 200)
