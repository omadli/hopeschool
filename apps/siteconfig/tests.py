"""Tests for apps.siteconfig."""
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.siteconfig.models import SiteConfig, SocialLink, TelegramRecipient

User = get_user_model()

_STATIC_STORAGE = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
    },
}


class SiteConfigModelTests(TestCase):
    """SiteConfig model behaviour."""

    def _get_config(self, **kwargs):
        """Fetch or create the singleton, update fields, save."""
        config = SiteConfig.get_solo()
        for k, v in kwargs.items():
            setattr(config, k, v)
        config.save()
        return config

    def test_str(self):
        config = SiteConfig.get_solo()
        self.assertEqual(str(config), "Sayt sozlamalari")

    def test_phone_normalization_spaced(self):
        config = self._get_config(phone_primary="+998 90 123 45 67")
        self.assertEqual(config.phone_primary, "+998901234567")

    def test_phone_normalization_9digit(self):
        config = self._get_config(phone_primary="901234567")
        self.assertEqual(config.phone_primary, "+998901234567")

    def test_phone_secondary_normalization(self):
        config = self._get_config(phone_secondary="+998 71 200 00 00")
        self.assertEqual(config.phone_secondary, "+998712000000")

    def test_blank_phone_stays_blank(self):
        config = self._get_config(phone_primary="", phone_secondary="")
        self.assertEqual(config.phone_primary, "")
        self.assertEqual(config.phone_secondary, "")

    def test_has_geo_false_when_empty(self):
        config = self._get_config(latitude="", longitude="")
        self.assertFalse(config.has_geo)

    def test_has_geo_true_when_set(self):
        config = self._get_config(latitude="41.299496", longitude="69.240073")
        self.assertTrue(config.has_geo)

    def test_google_map_src_contains_coords(self):
        config = self._get_config(latitude="41.299496", longitude="69.240073")
        self.assertIn("41.299496", config.google_map_src)
        self.assertIn("69.240073", config.google_map_src)

    def test_google_map_src_empty_without_coords(self):
        config = self._get_config(latitude="", longitude="")
        self.assertEqual(config.google_map_src, "")


@override_settings(STORAGES=_STATIC_STORAGE)
class SiteConfigAdminTests(TestCase):
    """Admin siteconfig pages return 200."""

    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="admin_siteconfig",
            password="adminpass123",
            email="admin_siteconfig@test.com",
        )
        self.client.force_login(self.superuser)

    def _get(self, url):
        return self.client.get(url, follow=True)

    def test_siteconfig_changelist(self):
        """Singleton admin changelist redirects to change page — follow=True → 200."""
        url = reverse("admin:siteconfig_siteconfig_changelist")
        self.assertEqual(self._get(url).status_code, 200)

    def test_siteconfig_change(self):
        """Singleton change page (pk=1 after get_solo())."""
        SiteConfig.get_solo()  # ensure the singleton exists
        url = reverse("admin:siteconfig_siteconfig_change", args=[1])
        self.assertEqual(self._get(url).status_code, 200)


# ---------------------------------------------------------------------------
# Phase F — repeatable SocialLink
# ---------------------------------------------------------------------------
class SocialLinkModelTests(TestCase):
    def test_str_uses_platform_when_no_label(self):
        s = SocialLink(platform="instagram", url="https://instagram.com/x")
        self.assertEqual(str(s), "Instagram")

    def test_str_uses_custom_label(self):
        s = SocialLink(platform="instagram", label="Bizning IG", url="https://instagram.com/x")
        self.assertEqual(str(s), "Bizning IG")

    def test_telegram_group_shares_telegram_icon(self):
        s = SocialLink(platform="telegram_group", url="https://t.me/g")
        self.assertEqual(s.icon_key, "telegram")

    def test_icon_key_default(self):
        s = SocialLink(platform="youtube", url="https://youtube.com/x")
        self.assertEqual(s.icon_key, "youtube")


@override_settings(STORAGES=_STATIC_STORAGE)
class SocialLinkRenderTests(TestCase):
    def test_link_renders_in_footer_and_jsonld(self):
        SocialLink.objects.create(
            platform="telegram", url="https://t.me/hope_demo", is_active=True)
        body = self.client.get("/uz/", follow=True).content.decode("utf-8", "replace")
        self.assertIn("https://t.me/hope_demo", body)      # footer icon link
        self.assertIn('"sameAs"', body)                     # JSON-LD block present

    def test_inactive_link_not_rendered(self):
        SocialLink.objects.create(
            platform="tiktok", url="https://tiktok.com/@hidden", is_active=False)
        body = self.client.get("/uz/", follow=True).content.decode("utf-8", "replace")
        self.assertNotIn("tiktok.com/@hidden", body)


@override_settings(STORAGES=_STATIC_STORAGE)
class SocialLinkAdminTests(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="admin_social", password="adminpass123", email="s@test.com")
        self.client.force_login(self.superuser)

    def test_changelist(self):
        url = reverse("admin:siteconfig_sociallink_changelist")
        self.assertEqual(self.client.get(url, follow=True).status_code, 200)

    def test_add(self):
        url = reverse("admin:siteconfig_sociallink_add")
        self.assertEqual(self.client.get(url, follow=True).status_code, 200)


# ---------------------------------------------------------------------------
# TelegramRecipient — multiple admins receive ariza notifications
# ---------------------------------------------------------------------------
class TelegramRecipientModelTests(TestCase):
    def test_str_prefers_name(self):
        r = TelegramRecipient(name="Direktor", chat_id="123456789")
        self.assertEqual(str(r), "Direktor")

    def test_str_falls_back_to_chat_id(self):
        r = TelegramRecipient(chat_id="123456789")
        self.assertEqual(str(r), "123456789")

    def test_numeric_chat_id_is_valid(self):
        r = TelegramRecipient(name="A", chat_id="123456789")
        r.full_clean()  # should not raise

    def test_negative_group_chat_id_is_valid(self):
        r = TelegramRecipient(name="Guruh", chat_id="-1001234567890")
        r.full_clean()

    def test_username_chat_id_is_valid(self):
        r = TelegramRecipient(name="Kanal", chat_id="@hope_admin")
        r.full_clean()

    def test_invalid_chat_id_rejected(self):
        r = TelegramRecipient(name="Bad", chat_id="not a chat id")
        with self.assertRaises(ValidationError):
            r.full_clean()


@override_settings(STORAGES=_STATIC_STORAGE)
class TelegramRecipientAdminTests(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="admin_tg", password="adminpass123", email="tg@test.com")
        self.client.force_login(self.superuser)

    def test_changelist(self):
        TelegramRecipient.objects.create(name="A", chat_id="111")
        url = reverse("admin:siteconfig_telegramrecipient_changelist")
        self.assertEqual(self.client.get(url, follow=True).status_code, 200)

    def test_add(self):
        url = reverse("admin:siteconfig_telegramrecipient_add")
        self.assertEqual(self.client.get(url, follow=True).status_code, 200)
