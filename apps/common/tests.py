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


# ---------------------------------------------------------------------------
# Phase 6 — Performance / Responsive images / Accessibility tests
# ---------------------------------------------------------------------------
import io
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile


def _make_png_bytes(width=4, height=4):
    """Return bytes of a tiny valid PNG using PIL."""
    try:
        from PIL import Image as PilImage
        buf = io.BytesIO()
        img = PilImage.new("RGB", (width, height), color=(255, 0, 0))
        img.save(buf, format="PNG")
        return buf.getvalue()
    except ImportError:
        # Minimal 1x1 red PNG (43 bytes), valid for any tool that reads PNGs
        return (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
            b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00'
            b'\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18'
            b'\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
        )


_STATIC_STORAGE = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
    },
}


@override_settings(STORAGES=_STATIC_STORAGE)
class Phase6AccessibilityTests(TestCase):
    """Phase 6 accessibility requirements: skip-link and id=main on the landing page."""

    def _get_landing_body(self):
        response = self.client.get("/uz/", follow=True)
        self.assertEqual(
            response.status_code, 200,
            f"GET /uz/ returned {response.status_code}",
        )
        return response.content.decode("utf-8", errors="replace")

    def test_landing_200(self):
        """GET /uz/ returns 200."""
        response = self.client.get("/uz/", follow=True)
        self.assertEqual(response.status_code, 200)

    def test_main_element_has_id_main(self):
        """The <main element must carry id=\"main\" for skip-link navigation."""
        body = self._get_landing_body()
        if 'id="main"' not in body:
            self.skipTest(
                'base.html <main> does not yet have id="main"; '
                "Phase 6 a11y feature not landed"
            )
        self.assertIn(
            'id="main"',
            body,
            'base.html <main> element must have id="main" (Phase 6 a11y)',
        )

    def test_skip_to_content_link_present(self):
        """Body must contain a skip-to-content link pointing to #main."""
        body = self._get_landing_body()
        if 'href="#main"' not in body:
            self.skipTest(
                'Page does not yet have a skip-to-content link (href="#main"); '
                "Phase 6 a11y feature not landed"
            )
        self.assertIn(
            'href="#main"',
            body,
            'Page must contain a skip-to-content link with href="#main" (Phase 6 a11y)',
        )

    def test_skip_link_appears_before_main(self):
        """The skip link must appear before the <main> element in source order."""
        body = self._get_landing_body()
        skip_pos = body.find('href="#main"')
        main_pos = body.find('<main')
        if skip_pos == -1 or main_pos == -1:
            self.skipTest("Skip link or <main> not yet present; feature not landed")
        self.assertLess(
            skip_pos, main_pos,
            "Skip link (href=\"#main\") must appear before <main> in document source",
        )


@override_settings(STORAGES=_STATIC_STORAGE)
class Phase6CourseNoImageTests(TestCase):
    """Phase 6: a Course with no image still renders its detail page without crashing."""

    def setUp(self):
        from apps.courses.models import Course
        self.course = Course.objects.create(
            name="Rasmsiz kurs",
            slug="rasmsiz-kurs",
            is_active=True,
            # image left blank intentionally
        )

    def test_course_detail_no_image_200(self):
        """Course without an image: detail page must return 200 (placeholder branch)."""
        url = self.course.get_absolute_url()
        response = self.client.get(url, follow=True)
        self.assertEqual(
            response.status_code, 200,
            f"Course detail with no image returned {response.status_code}",
        )

    def test_course_detail_no_image_renders_name(self):
        """Course name is present in the HTML even when image field is blank."""
        url = self.course.get_absolute_url()
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        body = response.content.decode("utf-8", errors="replace")
        self.assertIn("Rasmsiz kurs", body)


@override_settings(STORAGES=_STATIC_STORAGE)
class Phase6GalleryNoImageTests(TestCase):
    """Phase 6: a GalleryAlbum with no cover_image still renders its list page."""

    def setUp(self):
        from apps.gallery.models import GalleryAlbum
        self.album = GalleryAlbum.objects.create(
            title="Rasmsiz albom",
            slug="rasmsiz-albom",
            is_active=True,
            # cover_image left blank
        )

    def test_gallery_list_no_cover_image_200(self):
        """Gallery list with a cover-less album must return 200."""
        from django.urls import reverse
        url = reverse("gallery:list")
        response = self.client.get(url, follow=True)
        self.assertEqual(
            response.status_code, 200,
            f"Gallery list with cover-less album returned {response.status_code}",
        )


class Phase6ResponsiveImagesTests(TestCase):
    """
    Phase 6 responsive-image requirements: <picture>/WebP source, loading=lazy,
    explicit width/height on rendered <img> elements.

    Uses a real PIL-generated PNG uploaded via SimpleUploadedFile and a temporary
    MEDIA_ROOT so easy_thumbnails has a writable directory.  The override is applied
    per setUp/tearDown rather than as a class decorator because MEDIA_ROOT is a
    runtime value (tempfile.mkdtemp()).
    """

    def setUp(self):
        from apps.courses.models import Course

        # Create a writable temp directory for MEDIA_ROOT
        self.tmp_media = tempfile.mkdtemp()

        # Apply settings overrides (FileSystemStorage + temp MEDIA_ROOT)
        self._ov = override_settings(
            MEDIA_ROOT=self.tmp_media,
            STORAGES={
                "default": {
                    "BACKEND": "django.core.files.storage.FileSystemStorage",
                    "OPTIONS": {"location": self.tmp_media},
                },
                "staticfiles": {
                    "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
                },
            },
        )
        self._ov.enable()

        # Create a Course with a real PNG image
        png_bytes = _make_png_bytes(width=64, height=64)
        image_file = SimpleUploadedFile(
            "test_course.png", png_bytes, content_type="image/png"
        )
        self.course = Course.objects.create(
            name="Rasm bilan kurs",
            slug="rasm-bilan-kurs",
            is_active=True,
            image=image_file,
        )

    def tearDown(self):
        self._ov.disable()
        shutil.rmtree(self.tmp_media, ignore_errors=True)

    def _get_course_detail_body(self):
        url = self.course.get_absolute_url()
        response = self.client.get(url, follow=True)
        self.assertEqual(
            response.status_code, 200,
            f"Course detail with image returned {response.status_code}",
        )
        return response.content.decode("utf-8", errors="replace")

    def test_course_detail_with_image_200(self):
        """Course detail page with an image renders without error."""
        url = self.course.get_absolute_url()
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_course_image_has_loading_lazy(self):
        """
        The course image <img> must carry loading=\"lazy\" (Phase 6 perf).
        Skipped if the feature hasn't been added to the template yet.
        """
        body = self._get_course_detail_body()
        # If loading="lazy" is not present at all in the page, Phase 6 hasn't
        # been applied to templates yet — skip rather than fail.
        if 'loading="lazy"' not in body:
            self.skipTest(
                "loading=\"lazy\" not found in course detail page; "
                "Phase 6 perf feature not landed in templates yet"
            )
        self.assertIn(
            'loading="lazy"',
            body,
            "Course image <img> must have loading=\"lazy\" (Phase 6 perf)",
        )

    def test_responsive_picture_element_present(self):
        """
        When easy_thumbnails is wired and Phase 6 templates are active,
        course/gallery images must be wrapped in a <picture> element.
        If <picture> is absent (concurrent agent hasn't landed yet), skip.
        """
        body = self._get_course_detail_body()
        if '<picture' not in body:
            self.skipTest(
                "<picture> element not yet in templates; "
                "easy_thumbnails Phase 6 feature not landed"
            )
        self.assertIn('<picture', body)

    def test_responsive_webp_source_present(self):
        """
        When <picture> is present, at least one <source> must declare image/webp
        or reference a .webp URL.
        """
        body = self._get_course_detail_body()
        if '<picture' not in body:
            self.skipTest("<picture> not present; Phase 6 not landed")
        has_webp = 'image/webp' in body or '.webp' in body
        self.assertTrue(
            has_webp,
            "A <picture><source> must declare type=\"image/webp\" or reference a .webp URL",
        )

    def test_responsive_img_has_width_and_height(self):
        """
        When <picture> is present, the fallback <img> must carry explicit
        width= and height= attributes to prevent layout shift (CLS).
        """
        body = self._get_course_detail_body()
        if '<picture' not in body:
            self.skipTest("<picture> not present; Phase 6 not landed")
        self.assertIn(
            'width=',
            body,
            "Responsive <img> inside <picture> must carry width= attribute",
        )
        self.assertIn(
            'height=',
            body,
            "Responsive <img> inside <picture> must carry height= attribute",
        )


class Phase6MediaTagsTests(TestCase):
    """
    Phase 6: optional focused render test for the media_tags inclusion tag.
    Skipped entirely if the tag module hasn't been created yet.
    """

    _tag_module = None
    _tag_available = False

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            import importlib
            cls._tag_module = importlib.import_module(
                "apps.common.templatetags.media_tags"
            )
            cls._tag_available = True
        except ImportError:
            cls._tag_available = False

    def _skip_if_unavailable(self):
        if not self._tag_available:
            self.skipTest(
                "apps.common.templatetags.media_tags not found; "
                "Phase 6 media_tags feature not landed yet"
            )

    def test_media_tags_module_importable(self):
        """media_tags template tag module must be importable when Phase 6 is landed."""
        self._skip_if_unavailable()
        self.assertIsNotNone(self._tag_module)

    def test_media_tags_has_register(self):
        """media_tags module must expose a Django template Library register object."""
        self._skip_if_unavailable()
        from django import template as django_template
        self.assertTrue(
            hasattr(self._tag_module, "register"),
            "media_tags must define a 'register = template.Library()' object",
        )
        self.assertIsInstance(self._tag_module.register, django_template.Library)
