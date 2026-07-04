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


class DashboardSourceCardsTests(TestCase):
    """dashboard_callback builds per-source cards with every period precomputed
    (tabs switch client-side, so no ``?source_period=`` reload param)."""

    def _ctx(self):
        return dashboard_callback(RequestFactory().get("/admin/"), {})

    def _card(self, ctx, name):
        return next(c for c in ctx["source_cards"] if c["name"] == name)

    def test_default_period_is_all(self):
        self.assertEqual(self._ctx()["source_period"], "all")

    def test_card_counts_all_period(self):
        import json
        from apps.leads.models import Lead, LeadSource
        tg = LeadSource.objects.get(slug="telegram")
        Lead.objects.create(full_name="A", phone="+998901234567", source=tg)
        Lead.objects.create(full_name="B", phone="+998901234568", source=tg)
        card = self._card(self._ctx(), "Telegram")
        self.assertEqual(json.loads(card["counts_json"])["all"], 2)
        self.assertEqual(card["count"], 2)  # initial (no-JS) render value = all

    def test_card_link_and_percent(self):
        import json
        from apps.leads.models import Lead, LeadSource
        tg = LeadSource.objects.get(slug="telegram")
        Lead.objects.create(full_name="A", phone="+998901234567", source=tg)
        card = self._card(self._ctx(), "Telegram")
        self.assertIn("source=telegram", card["link"])
        self.assertEqual(json.loads(card["percents_json"])["all"], 100)
        self.assertEqual(card["percent"], 100)

    def test_periods_respect_time_windows(self):
        import json
        from datetime import timedelta

        from django.utils import timezone

        from apps.leads.models import Lead, LeadSource
        tg = LeadSource.objects.get(slug="telegram")
        Lead.objects.create(full_name="Now", phone="+998901234567", source=tg)
        old = Lead.objects.create(full_name="Old", phone="+998901234568", source=tg)
        # 8 days ago: outside today+week, inside 30+all. .update() bypasses
        # auto_now_add so we can backdate created_at.
        Lead.objects.filter(pk=old.pk).update(
            created_at=timezone.now() - timedelta(days=8)
        )
        counts = json.loads(self._card(self._ctx(), "Telegram")["counts_json"])
        self.assertEqual(counts["today"], 1)
        self.assertEqual(counts["week"], 1)
        self.assertEqual(counts["30"], 2)
        self.assertEqual(counts["all"], 2)

    def test_inactive_source_excluded_and_percent_rebased(self):
        import json
        from apps.leads.models import Lead, LeadSource
        tg = LeadSource.objects.get(slug="telegram")
        ig = LeadSource.objects.get(slug="instagram")
        # instagram gets a lead, then is deactivated -> it has no card
        Lead.objects.create(full_name="I", phone="+998901234500", source=ig)
        ig.is_active = False
        ig.save()
        Lead.objects.create(full_name="A", phone="+998901234567", source=tg)
        Lead.objects.create(full_name="B", phone="+998901234568", source=tg)
        ctx = self._ctx()
        names = [c["name"] for c in ctx["source_cards"]]
        self.assertNotIn("Instagram", names)  # inactive -> no card
        tg_card = self._card(ctx, "Telegram")
        # 2 telegram of 2 active-source leads = 100%, NOT 2/3 = 67%
        self.assertEqual(json.loads(tg_card["percents_json"])["all"], 100)


class DashboardDataTests(TestCase):
    """build_dashboard_data + _series bucketing across periods."""

    def _visit(self, when=None, **kw):
        from apps.analytics.models import VisitLog
        v = VisitLog.objects.create(path="/", device_type="mobile", **kw)
        if when is not None:
            VisitLog.objects.filter(pk=v.pk).update(created_at=when)  # bypass auto_now_add
        return v

    def _data(self, period):
        from apps.analytics.dashboard import build_dashboard_data
        return build_dashboard_data(RequestFactory().get("/admin/"), period)

    def test_clean_period_defaults_to_month(self):
        from apps.analytics.dashboard import clean_period
        self.assertEqual(clean_period("bogus"), "month")
        self.assertEqual(clean_period(None), "month")
        self.assertEqual(clean_period("year"), "year")

    def test_today_series_is_24_hourly_buckets(self):
        import json
        from django.utils import timezone
        now = timezone.now()
        self._visit(when=now)  # falls in current hour
        cfg = json.loads(self._data("today")["visits_chart"])
        self.assertEqual(len(cfg["labels"]), 24)
        self.assertEqual(cfg["labels"][0], "00")
        self.assertEqual(sum(cfg["datasets"][0]["data"]), 1)

    def test_week_series_is_7_daily_buckets(self):
        import json
        cfg = json.loads(self._data("week")["visits_chart"])
        self.assertEqual(len(cfg["labels"]), 7)

    def test_year_series_is_12_monthly_buckets(self):
        import json
        cfg = json.loads(self._data("year")["visits_chart"])
        self.assertEqual(len(cfg["labels"]), 12)

    def test_month_window_excludes_older_visits(self):
        from django.utils import timezone
        from datetime import timedelta
        now = timezone.now()
        self._visit(when=now)                       # in window
        self._visit(when=now - timedelta(days=40))  # outside month
        kpi = {k["icon"]: k["value"] for k in self._data("month")["kpis"]}
        self.assertEqual(kpi["visibility"], 1)      # Tashriflar (davr) KPI

    def test_week_series_excludes_out_of_window_visits(self):
        import json
        from django.utils import timezone
        from datetime import timedelta
        now = timezone.now()
        self._visit(when=now)                        # in window
        self._visit(when=now - timedelta(days=20))   # older than 7 days
        cfg = json.loads(self._data("week")["visits_chart"])
        self.assertEqual(len(cfg["labels"]), 7)
        self.assertEqual(sum(cfg["datasets"][0]["data"]), 1)  # only the in-window visit

    def test_source_cards_period_and_default(self):
        from apps.leads.models import Lead, LeadSource
        tg = LeadSource.objects.get(slug="telegram")
        Lead.objects.create(full_name="A", phone="+998901234567", source=tg)
        data = self._data("all")
        self.assertEqual(data["dash_period"], "all")
        tg_card = next(c for c in data["source_cards"] if c["name"] == "Telegram")
        self.assertEqual(tg_card["count"], 1)
        self.assertEqual(tg_card["percent"], 100)
        self.assertIn("source=telegram", tg_card["link"])
