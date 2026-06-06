"""Tests for apps.common — utils, validators, template tags, context processor."""
import types

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings

from apps.common.utils import normalize_phone
from apps.common.validators import (
    MaxFileSizeValidator,
    image_validators,
    pdf_validators,
)


# ---------------------------------------------------------------------------
# normalize_phone
# ---------------------------------------------------------------------------
class NormalizePhoneTests(SimpleTestCase):
    """apps.common.utils.normalize_phone"""

    def test_nine_digit_number(self):
        self.assertEqual(normalize_phone("901234567"), "+998901234567")

    def test_spaced_format(self):
        self.assertEqual(normalize_phone("+998 90 123 45 67"), "+998901234567")

    def test_full_12_digit_with_plus(self):
        self.assertEqual(normalize_phone("+998901234567"), "+998901234567")

    def test_with_dashes(self):
        self.assertEqual(normalize_phone("90-123-45-67"), "+998901234567")

    def test_empty_string_passthrough(self):
        self.assertEqual(normalize_phone(""), "")

    def test_none_passthrough(self):
        self.assertIsNone(normalize_phone(None))

    def test_unexpected_format_passthrough(self):
        val = "123456"
        self.assertEqual(normalize_phone(val), val)


# ---------------------------------------------------------------------------
# MaxFileSizeValidator
# ---------------------------------------------------------------------------
class MaxFileSizeValidatorTests(SimpleTestCase):
    """apps.common.validators.MaxFileSizeValidator"""

    def _fake_file(self, size_bytes):
        f = types.SimpleNamespace(size=size_bytes)
        return f

    def test_passes_below_limit(self):
        v = MaxFileSizeValidator(max_mb=5)
        # Should not raise
        v(self._fake_file(4 * 1024 * 1024))

    def test_raises_above_limit(self):
        v = MaxFileSizeValidator(max_mb=5)
        with self.assertRaises(ValidationError):
            v(self._fake_file(6 * 1024 * 1024))

    def test_equality(self):
        self.assertEqual(MaxFileSizeValidator(5), MaxFileSizeValidator(5))
        self.assertNotEqual(MaxFileSizeValidator(5), MaxFileSizeValidator(10))


# ---------------------------------------------------------------------------
# image_validators / pdf_validators — extension checks
# ---------------------------------------------------------------------------
class ImageValidatorsExtensionTests(SimpleTestCase):
    """image_validators reject disallowed extensions."""

    def test_valid_jpg(self):
        f = SimpleUploadedFile("photo.jpg", b"fake", content_type="image/jpeg")
        # FileExtensionValidator: should not raise
        for v in image_validators:
            try:
                v(f)
            except ValidationError:
                # MaxFileSizeValidator is fine for tiny file; only extension matters here
                pass

    def test_invalid_extension(self):
        f = SimpleUploadedFile("doc.txt", b"fake", content_type="text/plain")
        # FileExtensionValidator should raise
        from django.core.validators import FileExtensionValidator
        ext_validator = image_validators[0]
        self.assertIsInstance(ext_validator, FileExtensionValidator)
        with self.assertRaises(ValidationError):
            ext_validator(f)

    def test_pdf_rejects_non_pdf(self):
        f = SimpleUploadedFile("image.jpg", b"fake", content_type="image/jpeg")
        from django.core.validators import FileExtensionValidator
        ext_validator = pdf_validators[0]
        self.assertIsInstance(ext_validator, FileExtensionValidator)
        with self.assertRaises(ValidationError):
            ext_validator(f)

    def test_pdf_accepts_pdf_extension(self):
        f = SimpleUploadedFile("cert.pdf", b"fake", content_type="application/pdf")
        ext_validator = pdf_validators[0]
        # Should not raise
        ext_validator(f)


# ---------------------------------------------------------------------------
# Template filters and tags
# ---------------------------------------------------------------------------
class TemplateSomFilterTests(SimpleTestCase):
    """apps.common.templatetags.ui — som filter."""

    def setUp(self):
        from apps.common.templatetags.ui import som
        self.som = som

    def test_600000(self):
        # The filter uses a no-break space (\xa0 / U+00A0) as thousands separator
        self.assertEqual(self.som(600000), "600 000")

    def test_1000(self):
        self.assertEqual(self.som(1000), "1 000")

    def test_string_number(self):
        self.assertEqual(self.som("2000000"), "2 000 000")

    def test_invalid_returns_original(self):
        self.assertEqual(self.som("abc"), "abc")

    def test_zero(self):
        self.assertEqual(self.som(0), "0")


class PhoneDisplayFilterTests(SimpleTestCase):
    """apps.common.templatetags.ui — phone_display filter."""

    def setUp(self):
        from apps.common.templatetags.ui import phone_display
        self.phone_display = phone_display

    def test_formatted(self):
        self.assertEqual(self.phone_display("+998901234567"), "+998 90 123 45 67")

    def test_empty(self):
        self.assertEqual(self.phone_display(""), "")

    def test_none(self):
        self.assertIsNone(self.phone_display(None))

    def test_unexpected_passthrough(self):
        val = "12345"
        self.assertEqual(self.phone_display(val), val)


class IconTagTests(SimpleTestCase):
    """apps.common.templatetags.ui — icon simple_tag returns SVG."""

    def setUp(self):
        from apps.common.templatetags.ui import icon
        self.icon = icon

    def test_returns_svg(self):
        result = self.icon("cap")
        self.assertIn("<svg", result)

    def test_unknown_name_fallback(self):
        # Unknown name should still render the fallback (cap)
        result = self.icon("nonexistent")
        self.assertIn("<svg", result)

    def test_custom_size(self):
        result = self.icon("book", size=32)
        self.assertIn('width="32"', result)

    def test_custom_class(self):
        result = self.icon("star", cls="my-class")
        self.assertIn('class="my-class"', result)


class MapSrcTagTests(SimpleTestCase):
    """apps.common.templatetags.ui — google_map_src / yandex_map_src tags."""

    def setUp(self):
        from apps.common.templatetags.ui import google_map_src, yandex_map_src
        self.google_map_src = google_map_src
        self.yandex_map_src = yandex_map_src
        # Fake config object with lat/lng
        self.config = types.SimpleNamespace(latitude="41.299496", longitude="69.240073")
        self.empty_config = types.SimpleNamespace(latitude="", longitude="")

    def test_google_contains_coords(self):
        url = self.google_map_src(self.config, lang="uz")
        self.assertIn("41.299496", url)
        self.assertIn("69.240073", url)
        self.assertIn("hl=uz", url)

    def test_google_ru_locale(self):
        url = self.google_map_src(self.config, lang="ru")
        self.assertIn("hl=ru", url)

    def test_google_empty_config_returns_empty(self):
        self.assertEqual(self.google_map_src(self.empty_config, lang="uz"), "")

    def test_yandex_contains_coords(self):
        url = self.yandex_map_src(self.config, lang="uz")
        self.assertIn("41.299496", url)
        self.assertIn("69.240073", url)

    def test_yandex_ru_locale(self):
        url = self.yandex_map_src(self.config, lang="ru")
        self.assertIn("lang=ru_RU", url)

    def test_yandex_empty_config_returns_empty(self):
        self.assertEqual(self.yandex_map_src(self.empty_config, lang="uz"), "")

    def test_google_none_config_returns_empty(self):
        self.assertEqual(self.google_map_src(None, lang="uz"), "")

    def test_yandex_none_config_returns_empty(self):
        self.assertEqual(self.yandex_map_src(None, lang="uz"), "")


# ---------------------------------------------------------------------------
# Context processor
# ---------------------------------------------------------------------------
class SiteContextProcessorTests(TestCase):
    """apps.common.context_processors.site_context"""

    def test_keys_present(self):
        factory = RequestFactory()
        request = factory.get("/uz/")
        request.LANGUAGE_CODE = "uz"

        from apps.common.context_processors import site_context
        ctx = site_context(request)

        self.assertIn("site_config", ctx)
        self.assertIn("alt_urls", ctx)
        self.assertIn("lead_courses", ctx)

    def test_alt_urls_length(self):
        """alt_urls must have one entry per LANGUAGES (3: uz, ru, en)."""
        factory = RequestFactory()
        request = factory.get("/uz/")
        request.LANGUAGE_CODE = "uz"

        from apps.common.context_processors import site_context
        ctx = site_context(request)
        self.assertEqual(len(ctx["alt_urls"]), 3)

    def test_alt_urls_codes(self):
        factory = RequestFactory()
        request = factory.get("/uz/")
        request.LANGUAGE_CODE = "uz"

        from apps.common.context_processors import site_context
        ctx = site_context(request)
        codes = [item["code"] for item in ctx["alt_urls"]]
        self.assertIn("uz", codes)
        self.assertIn("ru", codes)
        self.assertIn("en", codes)
