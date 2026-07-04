"""Tests for apps.analytics — visit logging, staff exclusion, geo-IP, dashboard."""
from io import StringIO
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import RequestFactory, TestCase, override_settings

from apps.analytics import geoip
from apps.analytics.dashboard import dashboard_callback
from apps.analytics.models import VisitLog

User = get_user_model()

_STATIC_STORAGE = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}


class VisitLogModelTests(TestCase):
    def test_country_fields_exist(self):
        v = VisitLog()
        self.assertTrue(hasattr(v, "country"))
        self.assertTrue(hasattr(v, "country_code"))


@override_settings(STORAGES=_STATIC_STORAGE)
class StaffExclusionTests(TestCase):
    """Logged-in staff browsing the live site must NOT be counted; anons are."""

    def test_anonymous_visit_is_logged(self):
        self.assertEqual(VisitLog.objects.count(), 0)
        # A real, routable client IP — the middleware drops loopback/private IPs.
        self.client.get("/uz/", follow=True, REMOTE_ADDR="8.8.8.8")
        self.assertEqual(VisitLog.objects.filter(path="/uz/").count(), 1)

    def test_staff_visit_is_not_logged(self):
        staff = User.objects.create_user(
            username="staffer", password="pw12345678", is_staff=True)
        self.client.force_login(staff)
        self.client.get("/uz/", follow=True, REMOTE_ADDR="8.8.8.8")
        self.assertEqual(VisitLog.objects.filter(path="/uz/").count(), 0)

    def test_loopback_visit_is_not_logged(self):
        # Local dev traffic (127.0.0.1) must never reach the analytics table.
        self.client.get("/uz/", follow=True, REMOTE_ADDR="127.0.0.1")
        self.assertEqual(VisitLog.objects.filter(path="/uz/").count(), 0)

    @override_settings(DEBUG=True)
    def test_debug_mode_visit_is_not_logged(self):
        # In development (DEBUG=True) nothing is logged, even from a public IP.
        self.client.get("/uz/", follow=True, REMOTE_ADDR="8.8.8.8")
        self.assertEqual(VisitLog.objects.filter(path="/uz/").count(), 0)


@override_settings(STORAGES=_STATIC_STORAGE)
class AdminUrlExclusionTests(TestCase):
    """The (configurable) admin URL must never be counted as a public visit.

    The admin prefix is derived from settings.ADMIN_URL per request, so a custom
    ADMIN_URL is excluded too. Tested at the middleware level because the URLconf
    binds ADMIN_URL at import time — override_settings can't re-route the admin,
    but the middleware reads settings.ADMIN_URL live.
    """

    def _visit(self, path):
        from django.contrib.auth.models import AnonymousUser
        from django.http import HttpResponse

        from apps.analytics.middleware import VisitLogMiddleware
        # A public client IP — loopback/private IPs are dropped by the middleware.
        request = RequestFactory().get(path, REMOTE_ADDR="8.8.8.8")
        request.user = AnonymousUser()
        VisitLogMiddleware(lambda r: HttpResponse(status=200))(request)

    @override_settings(ADMIN_URL="kirma-bu-yerga/")
    def test_custom_admin_url_not_logged(self):
        self._visit("/kirma-bu-yerga/login/")
        self.assertEqual(VisitLog.objects.count(), 0)

    @override_settings(ADMIN_URL="admin/")
    def test_default_admin_url_not_logged(self):
        self._visit("/admin/login/")
        self.assertEqual(VisitLog.objects.count(), 0)

    @override_settings(ADMIN_URL="kirma-bu-yerga/")
    def test_public_path_still_logged(self):
        self._visit("/uz/")
        self.assertEqual(VisitLog.objects.filter(path="/uz/").count(), 1)


class GeoIpResolverTests(TestCase):
    def test_is_public_ip(self):
        self.assertTrue(geoip.is_public_ip("8.8.8.8"))
        self.assertFalse(geoip.is_public_ip("127.0.0.1"))
        self.assertFalse(geoip.is_public_ip("192.168.1.5"))
        self.assertFalse(geoip.is_public_ip("10.0.0.1"))
        self.assertFalse(geoip.is_public_ip("not-an-ip"))

    @patch("apps.analytics.geoip.requests.post")
    def test_resolve_ips_parses_batch(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: [
                {"status": "success", "query": "8.8.8.8",
                 "country": "United States", "countryCode": "US"},
                {"status": "fail", "query": "1.2.3.4"},
            ],
            raise_for_status=lambda: None,
        )
        result = geoip.resolve_ips(["8.8.8.8", "1.2.3.4", "127.0.0.1"])
        self.assertEqual(result, {"8.8.8.8": ("United States", "US")})
        # Private/loopback IPs are filtered out before the request payload.
        sent = mock_post.call_args.kwargs["json"]
        self.assertEqual([e["query"] for e in sent], ["8.8.8.8", "1.2.3.4"])

    @patch("apps.analytics.geoip.requests.post", side_effect=Exception("net down"))
    def test_resolve_ips_network_failure_is_empty(self, _mock):
        self.assertEqual(geoip.resolve_ips(["8.8.8.8"]), {})


class ResolveGeoipCommandTests(TestCase):
    @patch("apps.analytics.management.commands.resolve_geoip.resolve_ips")
    def test_command_backfills_country(self, mock_resolve):
        mock_resolve.return_value = {"8.8.8.8": ("Uzbekistan", "UZ")}
        VisitLog.objects.create(path="/uz/", method="GET", ip_address="8.8.8.8")
        VisitLog.objects.create(path="/ru/", method="GET", ip_address="8.8.8.8")
        call_command("resolve_geoip", stdout=StringIO())
        rows = VisitLog.objects.filter(ip_address="8.8.8.8")
        self.assertTrue(all(r.country == "Uzbekistan" and r.country_code == "UZ" for r in rows))

    @patch("apps.analytics.management.commands.resolve_geoip.resolve_ips")
    def test_command_noop_when_all_resolved(self, mock_resolve):
        VisitLog.objects.create(path="/uz/", method="GET",
                                ip_address="8.8.8.8", country="Uzbekistan")
        call_command("resolve_geoip", stdout=StringIO())
        mock_resolve.assert_not_called()


class DashboardCallbackTests(TestCase):
    def test_callback_returns_new_keys(self):
        ctx = dashboard_callback(RequestFactory().get("/admin/"), {})
        for key in ("kpis", "visits_chart", "device_chart", "leads_chart",
                    "leads_by_status", "top_countries", "content_inventory"):
            self.assertIn(key, ctx)

    def test_content_inventory_has_all_sections(self):
        ctx = dashboard_callback(RequestFactory().get("/admin/"), {})
        rows = ctx["content_inventory"]["rows"]
        self.assertEqual(len(rows), 6)  # courses, teachers, news, certs, testimonials, gallery
        for row in rows:
            self.assertEqual(len(row), 3)  # label, total, active

    def test_top_countries_reflects_resolved_visits(self):
        VisitLog.objects.create(path="/uz/", method="GET",
                                ip_address="8.8.8.8", country="Uzbekistan")
        ctx = dashboard_callback(RequestFactory().get("/admin/"), {})
        countries = [row[0] for row in ctx["top_countries"]["rows"]]
        self.assertIn("Uzbekistan", countries)


class DashboardSourceStatsTests(TestCase):
    """dashboard_callback builds per-source lead stats with a period filter."""

    def _ctx(self, period=None):
        from django.test import RequestFactory
        from apps.analytics.dashboard import dashboard_callback
        url = "/admin/" if not period else f"/admin/?source_period={period}"
        return dashboard_callback(RequestFactory().get(url), {})

    def test_source_stats_counts_leads(self):
        from apps.leads.models import Lead, LeadSource
        tg = LeadSource.objects.get(slug="telegram")
        Lead.objects.create(full_name="A", phone="+998901234567", source=tg)
        Lead.objects.create(full_name="B", phone="+998901234568", source=tg)
        ctx = self._ctx()
        by_name = {s["name"]: s["count"] for s in ctx["source_stats"]}
        self.assertEqual(by_name["Telegram"], 2)
        self.assertEqual(ctx["source_period"], "all")

    def test_source_stats_link_and_percent(self):
        from apps.leads.models import Lead, LeadSource
        tg = LeadSource.objects.get(slug="telegram")
        Lead.objects.create(full_name="A", phone="+998901234567", source=tg)
        tg_row = next(s for s in self._ctx()["source_stats"] if s["name"] == "Telegram")
        self.assertIn("source=telegram", tg_row["link"])
        self.assertEqual(tg_row["percent"], 100)

    def test_source_period_today_is_recorded(self):
        self.assertEqual(self._ctx("today")["source_period"], "today")
