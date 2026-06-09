"""Tests for apps.certificates — models, views, admin, CEFR import."""
import io
import tempfile
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from PIL import Image

from apps.certificates.models import Certificate
from apps.certificates.services import (
    CertificateImportError,
    parse_cefr,
    populate_certificate,
    render_first_page_jpeg,
)

User = get_user_model()


def _blank_pdf(width=300, height=420):
    """A minimal, valid 1-page PDF (no network, no PII) for render tests."""
    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(width=width, height=height)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()

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


# ---------------------------------------------------------------------------
# CEFR import — parser (pure function, no network/PII)
# ---------------------------------------------------------------------------
class ParseCefrTests(SimpleTestCase):
    def test_pymupdf_style_each_token_own_line(self):
        lines = ["24BBA1263659AA", "AD 4165352", "AZIMOV", "AMIN",
                 "SHERALI O‘G‘LI", "INGLIZ TILI", "B2", "62"]
        d = parse_cefr(lines)
        self.assertEqual(d["name"], "Azimov Amin Sherali o‘g‘li")
        self.assertEqual(d["level"], "B2")
        self.assertEqual(d["subject"], "INGLIZ TILI")
        self.assertEqual(d["serial"], "24BBA1263659AA")

    def test_pypdf_style_subject_and_level_merged(self):
        lines = ["24BBA1277677MM", "AD 6350889", "MARDONOV", "MIRFAYZBEK",
                 "JO‘RABEK O‘G‘LI", "INGLIZ TILI B2", "51 52"]
        d = parse_cefr(lines)
        self.assertEqual(d["name"], "Mardonov Mirfayzbek Jo‘rabek o‘g‘li")
        self.assertEqual(d["level"], "B2")
        self.assertEqual(d["subject"], "INGLIZ TILI")

    def test_qizi_suffix_lowercased(self):
        lines = ["25BBA1X", "AD 1", "SHUXRATOVA", "ZAHROBEGIM",
                 "SHERALI QIZI", "INGLIZ TILI B2"]
        self.assertEqual(parse_cefr(lines)["name"], "Shuxratova Zahrobegim Sherali qizi")

    def test_cyrillic_name_with_latin_subject(self):
        # Real-world variant: Cyrillic name, but the subject line is still Latin.
        lines = ["X", "AD 1", "САТТОРОВ", "АБДУСАТТОР",
                 "СОДИҚ ЎҒЛИ", "INGLIZ TILI B2"]
        self.assertEqual(parse_cefr(lines)["name"], "Сатторов Абдусаттор Содиқ ўғли")

    def test_no_subject_yields_empty_name(self):
        d = parse_cefr(["RANDOM", "TEXT", "HERE"])
        self.assertEqual(d["name"], "")


# ---------------------------------------------------------------------------
# CEFR import — render + orchestration (no network)
# ---------------------------------------------------------------------------
class RenderTests(SimpleTestCase):
    def test_render_returns_valid_jpeg(self):
        jpeg = render_first_page_jpeg(_blank_pdf())
        self.assertEqual(jpeg[:2], b"\xff\xd8", "JPEG magic bytes")
        Image.open(io.BytesIO(jpeg)).verify()


class PopulateCertificateTests(TestCase):
    def test_populate_sets_fields_and_image(self):
        cert = Certificate(external_url="https://example.com/cert.pdf")
        lines = ["24BBA1263659AA", "AD 4165352", "AZIMOV", "AMIN",
                 "SHERALI O‘G‘LI", "INGLIZ TILI", "B2"]
        with tempfile.TemporaryDirectory() as d, override_settings(MEDIA_ROOT=d):
            with mock.patch("apps.certificates.services.extract_text_lines",
                            return_value=lines):
                data = populate_certificate(
                    cert, fetcher=lambda url: _blank_pdf(), save=False
                )
        self.assertEqual(cert.student_name, "Azimov Amin Sherali o‘g‘li")
        self.assertEqual(cert.badge, "B2")
        self.assertIn("Ingliz tili", cert.description)
        self.assertTrue(cert.image.name.endswith(".jpg"))
        self.assertEqual(data["level"], "B2")

    def test_populate_requires_url(self):
        with self.assertRaises(CertificateImportError):
            populate_certificate(Certificate(external_url=""), fetcher=lambda u: b"")


# ---------------------------------------------------------------------------
# CEFR import — management command (mocked, idempotent)
# ---------------------------------------------------------------------------
class ImportCefrCommandTests(TestCase):
    @staticmethod
    def _fake_populate(cert, save=False):
        cert.student_name = "Test Talaba"
        cert.image = "certificates/cefr-test.jpg"  # path only; truthy, no file write
        if save:
            cert.save()
        return {"name": "Test Talaba", "level": "B2"}

    def test_command_creates_then_is_idempotent(self):
        from io import StringIO

        urls = ["https://example.com/a.pdf", "https://example.com/b.pdf"]
        target = "apps.certificates.management.commands.import_cefr.populate_certificate"

        with mock.patch(target, side_effect=self._fake_populate):
            call_command("import_cefr", *urls, stdout=StringIO(), stderr=StringIO())
        self.assertEqual(Certificate.objects.count(), 2)

        # Second run: images already set → skipped, no duplicate rows.
        with mock.patch(target, side_effect=self._fake_populate):
            call_command("import_cefr", *urls, stdout=StringIO(), stderr=StringIO())
        self.assertEqual(Certificate.objects.count(), 2)


# ---------------------------------------------------------------------------
# CEFR import — fetch guard (mocked requests)
# ---------------------------------------------------------------------------
class FetchPdfTests(SimpleTestCase):
    def _resp(self, content, ctype):
        resp = mock.Mock()
        resp.content = content
        resp.headers = {"Content-Type": ctype}
        resp.raise_for_status = mock.Mock()
        return resp

    def test_rejects_non_pdf_response(self):
        from apps.certificates.services import fetch_pdf_bytes

        with mock.patch("apps.certificates.services.requests.get",
                        return_value=self._resp(b"<html>no</html>", "text/html")):
            with self.assertRaises(CertificateImportError):
                fetch_pdf_bytes("https://example.com/x")

    def test_accepts_pdf_by_magic_bytes(self):
        from apps.certificates.services import fetch_pdf_bytes

        with mock.patch("apps.certificates.services.requests.get",
                        return_value=self._resp(b"%PDF-1.4\n...", "application/octet-stream")):
            self.assertTrue(fetch_pdf_bytes("https://example.com/x").startswith(b"%PDF"))
