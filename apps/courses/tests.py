"""Tests for apps.courses — models, views, admin."""
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.courses.models import Course, CourseCategory

User = get_user_model()

_STATIC_STORAGE = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
    },
}


class CourseModelTests(TestCase):
    """Course and CourseCategory model basics."""

    def setUp(self):
        self.category = CourseCategory.objects.create(
            name="Dasturlash",
            slug="dasturlash",
            is_active=True,
        )
        self.course = Course.objects.create(
            name="Python kursi",
            slug="python-kursi",
            is_active=True,
            category=self.category,
        )

    def test_course_str(self):
        self.assertEqual(str(self.course), "Python kursi")

    def test_category_str(self):
        self.assertEqual(str(self.category), "Dasturlash")

    def test_course_get_absolute_url(self):
        url = self.course.get_absolute_url()
        self.assertIn("python-kursi", url)
        self.assertIn("kurslar", url)

    def test_i18n_fields_exist(self):
        """modeltranslation creates _uz / _ru / _en name variants."""
        self.assertTrue(hasattr(self.course, "name_uz"))
        self.assertTrue(hasattr(self.course, "name_ru"))
        self.assertTrue(hasattr(self.course, "name_en"))

    def test_category_i18n_fields_exist(self):
        self.assertTrue(hasattr(self.category, "name_uz"))


@override_settings(STORAGES={
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
    },
})
class CourseDetailViewTests(TestCase):
    """Course detail view returns 200."""

    def setUp(self):
        self.course = Course.objects.create(
            name="Test kurs",
            slug="test-kurs",
            is_active=True,
        )

    def test_detail_view_200(self):
        url = self.course.get_absolute_url()
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_inactive_course_404(self):
        inactive = Course.objects.create(
            name="Yashirin kurs",
            slug="yashirin-kurs",
            is_active=False,
        )
        url = inactive.get_absolute_url()
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 404)


@override_settings(STORAGES={
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
    },
})
class CourseAdminTests(TestCase):
    """Admin changelist and add pages return 200 for courses."""

    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="admin_courses",
            password="adminpass123",
            email="admin_courses@test.com",
        )
        self.client.force_login(self.superuser)

    def _get(self, url):
        return self.client.get(url, follow=True)

    def test_course_changelist(self):
        url = reverse("admin:courses_course_changelist")
        self.assertEqual(self._get(url).status_code, 200)

    def test_course_add(self):
        url = reverse("admin:courses_course_add")
        self.assertEqual(self._get(url).status_code, 200)


# ---------------------------------------------------------------------------
# Phase E — course video + image gallery
# ---------------------------------------------------------------------------
@override_settings(STORAGES=_STATIC_STORAGE)
class CourseVideoTests(TestCase):
    def test_video_embed_renders_on_detail(self):
        course = Course.objects.create(
            name="Vid kurs", slug="vid-kurs", is_active=True,
            video_url="https://youtu.be/dQw4w9WgXcQ")
        body = self.client.get(course.get_absolute_url(), follow=True).content.decode(
            "utf-8", "replace")
        self.assertIn("youtube.com/embed/dQw4w9WgXcQ", body)

    def test_detail_with_images_renders(self):
        from apps.courses.models import CourseImage
        course = Course.objects.create(name="Galereyali kurs", slug="gal-kurs", is_active=True)
        CourseImage.objects.create(course=course, image="courses/gallery/a.jpg", is_active=True)
        resp = self.client.get(course.get_absolute_url(), follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Galereyali kurs", resp.content.decode("utf-8", "replace"))
