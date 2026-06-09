"""Tests for apps.leads — model, form, view, badges, admin."""
import json

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from apps.leads.badges import new_leads_count
from apps.leads.forms import LeadForm
from apps.leads.models import Lead
from apps.leads.views import _client_ip

User = get_user_model()

_STATIC_STORAGE = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
    },
}

LEAD_URL = "/ariza/"


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------
class LeadModelTests(TestCase):
    """Lead model — save() normalizes phone, __str__."""

    def test_save_normalizes_nine_digit_phone(self):
        lead = Lead.objects.create(full_name="Ali Valiyev", phone="901234567")
        self.assertEqual(lead.phone, "+998901234567")

    def test_save_normalizes_full_phone_with_spaces(self):
        lead = Lead.objects.create(full_name="Ali Valiyev", phone="+998 90 123 45 67")
        self.assertEqual(lead.phone, "+998901234567")

    def test_save_normalizes_full_phone_no_plus(self):
        lead = Lead.objects.create(full_name="Dilnoza", phone="998901234567")
        self.assertEqual(lead.phone, "+998901234567")

    def test_str_format(self):
        lead = Lead.objects.create(full_name="Test User", phone="+998901234567")
        # The em-dash separator matches models.py: f"{self.full_name} — {self.phone}"
        self.assertEqual(str(lead), "Test User — +998901234567")

    def test_default_status_is_new(self):
        lead = Lead.objects.create(full_name="Status Test", phone="+998901234567")
        self.assertEqual(lead.status, Lead.Status.NEW)

    def test_status_choices(self):
        self.assertIn("new", [c.value for c in Lead.Status])
        self.assertIn("contacted", [c.value for c in Lead.Status])
        self.assertIn("enrolled", [c.value for c in Lead.Status])
        self.assertIn("rejected", [c.value for c in Lead.Status])


# ---------------------------------------------------------------------------
# Form tests
# ---------------------------------------------------------------------------
class LeadFormTests(TestCase):
    """LeadForm — honeypot clean_website, phone validation."""

    _valid_data = {
        "full_name": "Kamola Qodirov",
        "phone": "+998901234567",
        "message": "",
        "website": "",  # honeypot empty (valid)
    }

    def test_valid_form_is_valid(self):
        form = LeadForm(data=self._valid_data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_honeypot_filled_raises_validation_error(self):
        data = {**self._valid_data, "website": "http://spam.com"}
        form = LeadForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("website", form.errors)

    def test_missing_phone_invalid(self):
        data = {**self._valid_data, "phone": ""}
        form = LeadForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("phone", form.errors)

    def test_bad_phone_format_invalid(self):
        data = {**self._valid_data, "phone": "12345"}
        form = LeadForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("phone", form.errors)

    def test_phone_normalized_on_clean(self):
        """9-digit phone is normalized to +998XXXXXXXXX by clean_phone."""
        data = {**self._valid_data, "phone": "901234567"}
        form = LeadForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["phone"], "+998901234567")

    def test_missing_full_name_invalid(self):
        data = {**self._valid_data, "full_name": ""}
        form = LeadForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("full_name", form.errors)


# ---------------------------------------------------------------------------
# View tests
# ---------------------------------------------------------------------------
class LeadCreateViewTests(TestCase):
    """POST /ariza/ — valid, honeypot, invalid, rate-limit."""

    _valid_data = {
        "full_name": "Bobur Toshmatov",
        "phone": "+998901234567",
        "message": "",
        "website": "",
    }

    def setUp(self):
        # Clear rate-limit counters so tests are deterministic.
        cache.clear()

    def tearDown(self):
        cache.clear()

    def _post(self, data=None):
        payload = data if data is not None else self._valid_data
        # Do NOT pass content_type here — the Django test client encodes dict
        # data as multipart/form-data by default, which the view reads fine.
        return self.client.post(LEAD_URL, payload)

    # --- URL resolves ---
    def test_url_resolves_to_lead_create(self):
        url = reverse("lead_create")
        self.assertEqual(url, LEAD_URL)

    # --- Valid submission ---
    def test_valid_post_returns_200_ok_true(self):
        response = self._post()
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["ok"])

    def test_valid_post_creates_lead(self):
        self._post()
        self.assertEqual(Lead.objects.count(), 1)

    def test_valid_post_normalizes_phone(self):
        data = {**self._valid_data, "phone": "901234567"}
        self._post(data=data)
        lead = Lead.objects.get()
        self.assertEqual(lead.phone, "+998901234567")

    def test_valid_post_stores_full_name(self):
        self._post()
        lead = Lead.objects.get()
        self.assertEqual(lead.full_name, "Bobur Toshmatov")

    # --- Honeypot ---
    def test_honeypot_returns_200_ok_true(self):
        data = {**self._valid_data, "website": "http://spam.com"}
        response = self._post(data=data)
        self.assertEqual(response.status_code, 200)
        body = json.loads(response.content)
        self.assertTrue(body["ok"])

    def test_honeypot_does_not_create_lead(self):
        data = {**self._valid_data, "website": "http://spam.com"}
        self._post(data=data)
        self.assertEqual(Lead.objects.count(), 0)

    # --- Missing required field ---
    def test_missing_phone_returns_400(self):
        data = {**self._valid_data, "phone": ""}
        response = self._post(data=data)
        self.assertEqual(response.status_code, 400)
        body = json.loads(response.content)
        self.assertFalse(body["ok"])
        self.assertIn("errors", body)

    def test_missing_phone_no_lead_created(self):
        data = {**self._valid_data, "phone": ""}
        self._post(data=data)
        self.assertEqual(Lead.objects.count(), 0)

    # --- Bad phone format ---
    def test_bad_phone_returns_400(self):
        data = {**self._valid_data, "phone": "12345"}
        response = self._post(data=data)
        self.assertEqual(response.status_code, 400)
        body = json.loads(response.content)
        self.assertFalse(body["ok"])

    def test_bad_phone_no_lead_created(self):
        data = {**self._valid_data, "phone": "12345"}
        self._post(data=data)
        self.assertEqual(Lead.objects.count(), 0)

    # --- GET is not allowed ---
    def test_get_not_allowed(self):
        response = self.client.get(LEAD_URL)
        self.assertEqual(response.status_code, 405)

    # --- UTM source captured ---
    def test_utm_source_captured(self):
        data = {**self._valid_data, "utm_source": "google"}
        self._post(data=data)
        lead = Lead.objects.get()
        self.assertEqual(lead.source, "google")

    # --- Rate limiting ---
    def test_rate_limit_allows_first_five_requests(self):
        """First RATE_LIMIT_MAX (5) valid POSTs all succeed."""
        for i in range(5):
            data = {
                "full_name": f"User {i}",
                "phone": "+998901234567",
                "message": "",
                "website": "",
            }
            response = self._post(data=data)
            self.assertEqual(
                response.status_code,
                200,
                f"Request {i + 1} should be 200, got {response.status_code}",
            )
        self.assertEqual(Lead.objects.count(), 5)

    def test_rate_limit_429_on_sixth_request(self):
        """After 5 valid POSTs, the 6th returns 429."""
        for i in range(5):
            data = {
                "full_name": f"User {i}",
                "phone": "+998901234567",
                "message": "",
                "website": "",
            }
            self._post(data=data)
        # 6th submission should be rate-limited
        response = self._post()
        self.assertEqual(response.status_code, 429)
        body = json.loads(response.content)
        self.assertFalse(body["ok"])
        # No new lead created on the 6th request
        self.assertEqual(Lead.objects.count(), 5)


# ---------------------------------------------------------------------------
# Client-IP resolution (anti-spoof for the rate-limit)
# ---------------------------------------------------------------------------
class ClientIpTests(SimpleTestCase):
    """_client_ip reads the real peer from the RIGHT of X-Forwarded-For."""

    def _req(self, xff=None, remote="10.0.0.1"):
        req = RequestFactory().post(LEAD_URL)
        req.META["REMOTE_ADDR"] = remote
        if xff is not None:
            req.META["HTTP_X_FORWARDED_FOR"] = xff
        return req

    def test_no_xff_falls_back_to_remote_addr(self):
        self.assertEqual(_client_ip(self._req(remote="10.0.0.5")), "10.0.0.5")

    def test_single_proxy_uses_last_xff_entry(self):
        # nginx appends the real peer; the client-supplied prefix is ignored.
        self.assertEqual(_client_ip(self._req(xff="1.2.3.4, 9.9.9.9")), "9.9.9.9")

    def test_spoofed_prefix_does_not_change_the_key(self):
        a = _client_ip(self._req(xff="1.1.1.1, 9.9.9.9"))
        b = _client_ip(self._req(xff="2.2.2.2, 9.9.9.9"))
        self.assertEqual(a, b, "Forged XFF prefix must not yield a different IP")

    @override_settings(TRUSTED_PROXY_COUNT=2)
    def test_two_proxies_skip_the_extra_hop(self):
        # client, real-edge(nginx-seen), cdn-to-origin → real client is -2.
        self.assertEqual(
            _client_ip(self._req(xff="9.9.9.9, 8.8.8.8, 7.7.7.7")), "8.8.8.8"
        )


# ---------------------------------------------------------------------------
# Badge tests
# ---------------------------------------------------------------------------
class LeadBadgeTests(TestCase):
    """badges.new_leads_count — returns count of status='new' leads."""

    def test_empty_returns_empty_string(self):
        result = new_leads_count(request=None)
        self.assertEqual(result, "")

    def test_returns_count_of_new_leads(self):
        Lead.objects.create(full_name="A", phone="+998901234567", status=Lead.Status.NEW)
        Lead.objects.create(full_name="B", phone="+998901234568", status=Lead.Status.NEW)
        result = new_leads_count(request=None)
        self.assertEqual(result, "2")

    def test_non_new_leads_not_counted(self):
        Lead.objects.create(full_name="A", phone="+998901234567", status=Lead.Status.NEW)
        Lead.objects.create(full_name="B", phone="+998901234568", status=Lead.Status.CONTACTED)
        Lead.objects.create(full_name="C", phone="+998901234569", status=Lead.Status.ENROLLED)
        result = new_leads_count(request=None)
        self.assertEqual(result, "1")

    def test_all_contacted_returns_empty_string(self):
        Lead.objects.create(full_name="A", phone="+998901234567", status=Lead.Status.CONTACTED)
        result = new_leads_count(request=None)
        self.assertEqual(result, "")

    def test_returns_string_type(self):
        Lead.objects.create(full_name="A", phone="+998901234567", status=Lead.Status.NEW)
        result = new_leads_count(request=None)
        self.assertIsInstance(result, str)


# ---------------------------------------------------------------------------
# Admin tests
# ---------------------------------------------------------------------------
@override_settings(STORAGES=_STATIC_STORAGE)
class LeadAdminTests(TestCase):
    """Admin changelist for leads returns 200 for superusers."""

    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="admin_leads",
            password="adminpass123",
            email="admin_leads@test.com",
        )
        self.client.force_login(self.superuser)

    def test_lead_changelist_returns_200(self):
        url = reverse("admin:leads_lead_changelist")
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_lead_changelist_with_entries_returns_200(self):
        Lead.objects.create(full_name="Test", phone="+998901234567")
        url = reverse("admin:leads_lead_changelist")
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_lead_detail_returns_200(self):
        lead = Lead.objects.create(full_name="Admin Detail", phone="+998901234567")
        url = reverse("admin:leads_lead_change", args=[lead.pk])
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
