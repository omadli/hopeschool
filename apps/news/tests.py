"""Tests for apps.news — models, views, admin."""
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.news.models import NewsPost

User = get_user_model()

_STATIC_STORAGE = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
    },
}


class NewsPostModelTests(TestCase):
    """NewsPost model basics."""

    def setUp(self):
        self.post = NewsPost.objects.create(
            title="Test yangilik",
            slug="test-yangilik",
            is_published=True,
        )

    def test_str(self):
        self.assertEqual(str(self.post), "Test yangilik")

    def test_get_absolute_url(self):
        url = self.post.get_absolute_url()
        self.assertIn("test-yangilik", url)
        self.assertIn("yangiliklar", url)

    def test_i18n_fields_exist(self):
        self.assertTrue(hasattr(self.post, "title_uz"))
        self.assertTrue(hasattr(self.post, "title_ru"))
        self.assertTrue(hasattr(self.post, "title_en"))


@override_settings(STORAGES=_STATIC_STORAGE)
class NewsViewTests(TestCase):
    """News list and detail views return 200."""

    def setUp(self):
        self.post = NewsPost.objects.create(
            title="Sayt ochildi",
            slug="sayt-ochildi",
            is_published=True,
        )

    def test_list_view_200(self):
        url = reverse("news:list")
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_detail_view_200(self):
        url = self.post.get_absolute_url()
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_unpublished_post_404(self):
        draft = NewsPost.objects.create(
            title="Qoralama",
            slug="qoralama",
            is_published=False,
        )
        url = draft.get_absolute_url()
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 404)


@override_settings(STORAGES=_STATIC_STORAGE)
class NewsAdminTests(TestCase):
    """Admin changelist and add pages return 200 for news."""

    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="admin_news",
            password="adminpass123",
            email="admin_news@test.com",
        )
        self.client.force_login(self.superuser)

    def _get(self, url):
        return self.client.get(url, follow=True)

    def test_newspost_changelist(self):
        url = reverse("admin:news_newspost_changelist")
        self.assertEqual(self._get(url).status_code, 200)

    def test_newspost_add(self):
        url = reverse("admin:news_newspost_add")
        self.assertEqual(self._get(url).status_code, 200)

    def test_ckeditor_richer_toolbar_config(self):
        """The expanded CKEditor toolbar config must reach the change form."""
        html = self._get(reverse("admin:news_newspost_add")).content.decode("utf-8", "replace")
        for item in ("mediaEmbed", "fontColor", "insertTable"):
            self.assertIn(item, html)

    def test_ckeditor_toolbar_has_no_source_editing(self):
        """sourceEditing lets an admin paste raw HTML (incl. <script>) past the
        editor's own escaping straight into a |safe-rendered field — dropped."""
        html = self._get(reverse("admin:news_newspost_add")).content.decode("utf-8", "replace")
        self.assertNotIn("sourceEditing", html)


# ---------------------------------------------------------------------------
# Phase E — news video
# ---------------------------------------------------------------------------
@override_settings(STORAGES=_STATIC_STORAGE)
class NewsVideoTests(TestCase):
    def test_video_embed_renders_on_detail(self):
        post = NewsPost.objects.create(
            title="Vid yangilik", slug="vid-yangilik", is_published=True,
            video_url="https://vimeo.com/123456789")
        body = self.client.get(post.get_absolute_url(), follow=True).content.decode(
            "utf-8", "replace")
        self.assertIn("player.vimeo.com/video/123456789", body)
