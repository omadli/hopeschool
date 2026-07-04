# Global Dashboard Time Filter — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a top-of-dashboard time filter (Bugun/Hafta/Oy/Yil/Jami) that AJAX-refreshes every time-based widget for the selected period.

**Architecture:** `build_dashboard_data(request, period)` computes all period widgets (KPIs, chart JSON configs, tables, device doughnut+legend, CRM source cards). The page and a new staff-only AJAX view both render one partial (`_dashboard_content.html`). Charts are our own `<canvas data-dash-chart>` driven by `admin_dashboard.js` (global Chart.js + a small point-label plugin), so a filter click swaps the partial HTML and re-inits charts — no reload.

**Tech Stack:** Django 5, django-unfold, Chart.js (bundled by Unfold, global `Chart`), vanilla JS. Tests: Django `TestCase`.

## Global Constraints

- **Periods:** `today`, `week`, `month`, `year`, `all`. Default = `month`. Invalid → `month`.
- **Granularity (line charts):** today→hourly (24), week→daily (7), month→daily (30), year→monthly (12), all→monthly (since first record).
- **Point labels:** shown on line charts; when a series has >16 points, show every `ceil(n/12)`-th (plus the last).
- **CRM source cards are driven by the global filter** — they have NO own period tabs anymore.
- **Static (not filtered):** the "Sayt kontenti" inventory only. Everything else is period-driven.
- **Admin CSS constraint:** the admin has NO project Tailwind build — only Unfold's precompiled `venv/Lib/site-packages/unfold/static/unfold/css/styles.css` utilities work. PRESENT: `flex items-center justify-center`, `mt-2`, `gap-4`, `object-cover`, `transition-all`, `rounded-2xl`, `grid-cols-1..9`, `text-2xl`, `overflow-hidden`, `bg-primary-600`, `text-primary-600`, `border-base-200`. ABSENT (do NOT use): `place-items-center`, `mt-2.5`, `object-contain`, `transition-[width]`, `duration-500`. When in doubt, `grep '\.<class>{' <that file>` before using a class, or use inline `style="..."`.
- **Django comments:** never multi-line `{# … #}` (leaks as page text); single-line or `{% comment %}`.
- **Test/run:** venv Python `venv/Scripts/python.exe`; dev server `python manage.py runserver 8001`.
- Run commands from repo root `D:\Projects\hopeschool`.

---

## File Structure

| File | Responsibility | Action |
|---|---|---|
| `apps/analytics/dashboard.py` | period helpers, `_series`, chart JSON builders, `build_dashboard_data`; `dashboard_callback` delegates | Modify |
| `apps/analytics/views.py` | `dashboard_data` AJAX view | Create |
| `config/urls.py` | `dashboard-data/` URL under admin prefix | Modify |
| `templates/admin/_dashboard_content.html` | all period widgets partial | Create |
| `templates/admin/index.html` | filter bar + `#dashboard-content` wrapper + static inventory + script | Modify |
| `static/js/admin_dashboard.js` | own Chart.js init + point-label plugin + AJAX filter | Create |
| `config/settings.py` | add `admin_dashboard.js` to `UNFOLD["SCRIPTS"]` | Modify |
| `apps/analytics/tests.py` | series/build_data/view tests | Modify |

---

## Task 1: Data layer — periods, granularity, `build_dashboard_data`

**Files:**
- Modify: `apps/analytics/dashboard.py` (additive — keep the existing `_build_context`/`dashboard_callback` working until Task 2)
- Test: `apps/analytics/tests.py`

**Interfaces:**
- Produces (consumed by Tasks 2 & 3):
  - `PERIODS = ("today","week","month","year","all")`, `DEFAULT_PERIOD = "month"`
  - `clean_period(value) -> str`
  - `period_qs(qs, period, now, today) -> QuerySet` (window filter)
  - `_series(qs, period, now, today) -> (labels: list[str], data: list[int])`
  - `build_dashboard_data(request, period) -> dict` with keys: `dash_period, kpis, visits_chart, leads_chart, device_chart, device_legend, top_paths, top_referrers, top_countries, leads_by_status, source_cards`
  - chart JSON contract: line = `{"type":"line","labels":[...],"datasets":[{"label":str,"data":[...],"line":"primary-500","fill":"primary-100"}],"showLabels":true}`; doughnut = `{"type":"doughnut","labels":[...],"datasets":[{"data":[...],"colors":["primary-500",...]}]}`

- [ ] **Step 1: Write failing tests**

Add to `apps/analytics/tests.py` (module already imports `RequestFactory`, `dashboard_callback`; add `TestCase` is present). Append this class:

```python
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
```

- [ ] **Step 2: Run tests, verify they fail**

Run: `venv/Scripts/python.exe manage.py test apps.analytics.tests.DashboardDataTests -v 2`
Expected: FAIL — `ImportError: cannot import name 'build_dashboard_data'` / `clean_period`.

- [ ] **Step 3: Add the period + series helpers to `dashboard.py`**

At the top of `apps/analytics/dashboard.py`, extend the imports:

```python
import json
from datetime import timedelta

from django.db.models import Count, Min
from django.db.models.functions import TruncDate, TruncHour, TruncMonth
from django.utils import timezone
from django.utils.translation import get_language, gettext_lazy as _

from .models import VisitLog
```

Below the existing `_DEVICE_*` constants add:

```python
PERIODS = ("today", "week", "month", "year", "all")
DEFAULT_PERIOD = "month"

# Doughnut/legend colours as Unfold CSS-variable *keys* (resolved to rgb in JS
# for the canvas; the legend HTML wraps each in var(--color-<key>)).
_DEVICE_COLOR_KEYS = ["primary-500", "primary-300", "primary-700", "base-400", "base-300"]


def clean_period(value):
    """Whitelist a requested period, defaulting to month."""
    return value if value in PERIODS else DEFAULT_PERIOD


def period_qs(qs, period, now, today):
    """Filter a queryset to the period's rolling window (created_at)."""
    if period == "today":
        return qs.filter(created_at__date=today)
    if period == "week":
        return qs.filter(created_at__gte=now - timedelta(days=7))
    if period == "month":
        return qs.filter(created_at__gte=now - timedelta(days=30))
    if period == "year":
        return qs.filter(created_at__gte=now - timedelta(days=365))
    return qs  # all


def _month_first(d):
    return d.replace(day=1)


def _month_range(end_first, count):
    """`count` first-of-month dates ending at end_first (ascending)."""
    months, y, m = [], end_first.year, end_first.month
    for _i in range(count):
        months.append(end_first.replace(year=y, month=m, day=1))
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    return list(reversed(months))


def _bucket_keys(qs, period, now, today):
    """Return (granularity, [(key, label), ...]) ordered buckets for the period."""
    if period == "today":
        return "hour", [(h, f"{h:02d}") for h in range(24)]
    if period == "week":
        days = [today - timedelta(days=i) for i in range(6, -1, -1)]
        return "day", [(d, d.strftime("%d.%m")) for d in days]
    if period == "month":
        days = [today - timedelta(days=i) for i in range(29, -1, -1)]
        return "day", [(d, d.strftime("%d.%m")) for d in days]
    if period == "year":
        months = _month_range(_month_first(today), 12)
        return "month", [(m, m.strftime("%m.%y")) for m in months]
    # all: from the earliest record's month to this month (fallback 12)
    first = qs.aggregate(m=Min("created_at"))["m"]
    if not first:
        months = _month_range(_month_first(today), 12)
    else:
        start = _month_first(timezone.localtime(first).date())
        count = (today.year - start.year) * 12 + (today.month - start.month) + 1
        months = _month_range(_month_first(today), max(count, 1))
    return "month", [(m, m.strftime("%m.%y")) for m in months]


def _series(qs, period, now, today):
    """(labels, data) — counts bucketed by the period's granularity, gap-filled."""
    gran, keys_labels = _bucket_keys(qs, period, now, today)
    labels = [lbl for _k, lbl in keys_labels]
    if gran == "hour":
        rows = (qs.filter(created_at__date=today)
                  .annotate(b=TruncHour("created_at")).values("b").annotate(t=Count("id")))
        counts = {timezone.localtime(r["b"]).hour: r["t"] for r in rows}
        return labels, [counts.get(h, 0) for h, _l in keys_labels]
    if gran == "day":
        rows = qs.annotate(b=TruncDate("created_at")).values("b").annotate(t=Count("id"))
        counts = {r["b"]: r["t"] for r in rows}
        return labels, [counts.get(d, 0) for d, _l in keys_labels]
    rows = qs.annotate(b=TruncMonth("created_at")).values("b").annotate(t=Count("id"))
    counts = {timezone.localtime(r["b"]).date().replace(day=1): r["t"] for r in rows}
    return labels, [counts.get(m, 0) for m, _l in keys_labels]


def _line_json(label, labels, data):
    return json.dumps({
        "type": "line",
        "labels": labels,
        "datasets": [{"label": str(label), "data": data, "line": "primary-500", "fill": "primary-100"}],
        "showLabels": True,
    })


def _doughnut_json(labels, data, color_keys):
    return json.dumps({
        "type": "doughnut",
        "labels": [str(l) for l in labels],
        "datasets": [{"data": data, "colors": color_keys}],
    })
```

- [ ] **Step 4: Add `build_dashboard_data` to `dashboard.py`**

Add this function (it reuses the helpers above; it does NOT touch the existing `_build_context` yet):

```python
def build_dashboard_data(request, period):
    """All period-dependent dashboard widgets for `period`. Defensive: returns
    zeroed widgets if the analytics/leads tables are unavailable."""
    period = clean_period(period)
    data = {"dash_period": period}
    try:
        from apps.courses.models import Course
        from apps.leads.models import Lead, LeadSource
        from apps.siteconfig.models import SiteConfig
        from apps.teachers.models import Teacher

        now = timezone.now()
        today = timezone.localdate()
        visits = VisitLog.objects.all()
        leads = Lead.objects.all()
        pv = period_qs(visits, period, now, today)
        pl = period_qs(leads, period, now, today)

        # KPIs (period-aware, + static totals)
        data["kpis"] = [
            {"title": _("Tashriflar (davr)"), "value": pv.count(), "icon": "visibility"},
            {"title": _("Arizalar (davr)"), "value": pl.count(), "icon": "mail"},
            {"title": _("Yangi arizalar (davr)"),
             "value": pl.filter(status=Lead.Status.NEW).count(), "icon": "inbox"},
            {"title": _("Kurslar / oʻqituvchilar"),
             "value": f"{Course.objects.count()} / {Teacher.objects.count()}", "icon": "school"},
        ]

        # Line charts (series applies its own bucket window)
        data["visits_chart"] = _line_json(_("Tashriflar"), *_series(visits, period, now, today))
        data["leads_chart"] = _line_json(_("Arizalar"), *_series(leads, period, now, today))

        # Device doughnut + legend (period-filtered)
        drows = list(pv.values("device_type").annotate(total=Count("id")).order_by("-total"))
        dlabels = [str(_DEVICE_LABELS.get(r["device_type"], r["device_type"])) for r in drows]
        ddata = [r["total"] for r in drows]
        dkeys = _DEVICE_COLOR_KEYS[: len(ddata)] or _DEVICE_COLOR_KEYS
        data["device_chart"] = _doughnut_json(dlabels, ddata, dkeys)
        dtotal = sum(ddata) or 1
        data["device_legend"] = [
            {"label": dlabels[i], "count": r["total"], "percent": round(r["total"] * 100 / dtotal),
             "color": f"var(--color-{dkeys[i % len(dkeys)]})",
             "icon": _DEVICE_ICONS.get(r["device_type"], "devices_other")}
            for i, r in enumerate(drows)
        ]

        # Tables (period-filtered)
        data["top_paths"] = {
            "headers": [str(_("Sahifa")), str(_("Tashriflar"))],
            "rows": [[p["path"], p["total"]] for p in
                     pv.values("path").annotate(total=Count("id")).order_by("-total")[:5]],
        }
        data["top_referrers"] = {
            "headers": [str(_("Manba")), str(_("Tashriflar"))],
            "rows": [[r["referrer"], r["total"]] for r in
                     pv.exclude(referrer="").values("referrer").annotate(total=Count("id")).order_by("-total")[:5]],
        }
        data["top_countries"] = {
            "headers": [str(_("Davlat")), str(_("Tashriflar"))],
            "rows": [[r["country"], r["total"]] for r in
                     pv.exclude(country="").values("country").annotate(total=Count("id")).order_by("-total")[:8]],
        }
        status_labels = dict(Lead.Status.choices)
        data["leads_by_status"] = {
            "headers": [str(_("Holat")), str(_("Soni"))],
            "rows": [[str(status_labels.get(r["status"], r["status"])), r["total"]] for r in
                     pl.values("status").annotate(total=Count("id")).order_by("-total")],
        }

        # CRM source cards (period-filtered, denominator = shown active sources)
        counts = {r["source"]: r["total"]
                  for r in pl.values("source").annotate(total=Count("id"))}
        active = list(LeadSource.objects.filter(is_active=True))
        total_src = sum(counts.get(s.id, 0) for s in active) or 1
        try:
            domain = SiteConfig.get_solo().site_domain or request.get_host()
        except Exception:  # pragma: no cover - defensive
            domain = request.get_host()
        lang = get_language() or "uz"
        data["source_cards"] = [{
            "name": s.name, "count": counts.get(s.id, 0),
            "percent": round(counts.get(s.id, 0) * 100 / total_src),
            "link": s.build_link(domain, lang),
            "image": s.image.url if s.image else "",
            "brand": s.brand_key, "icon": s.icon or "hub", "color": s.color or "",
        } for s in active]
    except Exception:  # pragma: no cover - defensive (unmigrated tables)
        data.setdefault("kpis", [])
        for k in ("visits_chart", "leads_chart", "device_chart"):
            data.setdefault(k, json.dumps({"type": "line", "labels": [], "datasets": []}))
        data.setdefault("device_legend", [])
        for k in ("top_paths", "top_referrers", "top_countries", "leads_by_status"):
            data.setdefault(k, {"headers": [], "rows": []})
        data.setdefault("source_cards", [])
    return data
```

- [ ] **Step 5: Run tests, verify they pass**

Run: `venv/Scripts/python.exe manage.py test apps.analytics.tests.DashboardDataTests -v 2`
Expected: PASS (6 tests). Note `test_month_window_excludes_older_visits` keys off the `visibility` KPI icon.

- [ ] **Step 6: Commit**

```bash
git add apps/analytics/dashboard.py apps/analytics/tests.py
git commit -m "feat(dashboard): period-aware data layer (build_dashboard_data, _series)"
```

---

## Task 2: Template switch — content partial, filter bar, callback rewire

**Files:**
- Create: `templates/admin/_dashboard_content.html`
- Modify: `templates/admin/index.html`, `apps/analytics/dashboard.py` (rewire `dashboard_callback`; remove the old `_build_context` body and CRM inline logic)
- Test: `apps/analytics/tests.py`

**Interfaces:**
- Consumes: `build_dashboard_data`, `clean_period`, `DEFAULT_PERIOD` (Task 1).
- Produces: the admin index renders the filter bar + `#dashboard-content` for `?period=` (default month), server-side, no JS. Canvas elements `[data-dash-chart]` carry chart JSON. Static "Sayt kontenti" stays outside `#dashboard-content`.

- [ ] **Step 1: Write the failing test**

Add to `apps/analytics/tests.py`:

```python
@override_settings(STORAGES=_STATIC_STORAGE)
class DashboardIndexRenderTests(TestCase):
    """The admin index renders the new filter bar + content for a period."""

    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="dash_admin", password="pass12345", email="d@test.com")
        self.client.force_login(self.admin)

    def test_index_has_filter_and_content(self):
        resp = self.client.get(reverse("admin:index") + "?period=week", follow=True)
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        self.assertIn('data-dash-tabs', html)          # filter bar present
        self.assertIn('id="dashboard-content"', html)   # swappable wrapper
        self.assertIn('data-dash-chart', html)          # our own chart canvas
        self.assertIn('data-period="week"', html)
```

`reverse`, `User`, `override_settings`, `_STATIC_STORAGE` already exist in this test module.

- [ ] **Step 2: Run test, verify it fails**

Run: `venv/Scripts/python.exe manage.py test apps.analytics.tests.DashboardIndexRenderTests -v 2`
Expected: FAIL — `data-dash-tabs` not in HTML (old dashboard still rendered).

- [ ] **Step 3: Rewire `dashboard_callback` in `dashboard.py`**

Replace the ENTIRE existing `_build_context(...)` function AND the existing `dashboard_callback(...)` function (everything from `def _build_context` to the end of the file) with:

```python
def _content_inventory():
    """Static (non-time) content totals — not affected by the period filter."""
    from apps.certificates.models import Certificate
    from apps.courses.models import Course
    from apps.gallery.models import GalleryImage
    from apps.news.models import NewsPost
    from apps.teachers.models import Teacher
    from apps.testimonials.models import Testimonial

    inventory = [
        (_("Kurslar"), Course.objects, {"is_active": True}),
        (_("Oʻqituvchilar"), Teacher.objects, {"is_active": True}),
        (_("Yangiliklar"), NewsPost.objects, {"is_published": True}),
        (_("Sertifikatlar"), Certificate.objects, {"is_active": True}),
        (_("Fikrlar"), Testimonial.objects, {"is_active": True}),
        (_("Galereya rasmlari"), GalleryImage.objects, {"is_active": True}),
    ]
    return {
        "headers": [str(_("Boʻlim")), str(_("Jami")), str(_("Faol / chop etilgan"))],
        "rows": [[str(label), mgr.count(), mgr.filter(**flt).count()]
                 for label, mgr, flt in inventory],
    }


def dashboard_callback(request, context):
    """Unfold index callback — renders the default (or ?period=) period."""
    period = clean_period(request.GET.get("period"))
    context.update(build_dashboard_data(request, period))
    try:
        context["content_inventory"] = _content_inventory()
    except Exception:  # pragma: no cover - defensive
        context.setdefault("content_inventory", {"headers": [], "rows": []})
    return context
```

- [ ] **Step 4: Create the content partial**

Create `templates/admin/_dashboard_content.html`:

```html
{% load i18n unfold ui %}
{# ---- KPI cards ---- #}
<div class="grid grid-cols-2 gap-3 mb-8 sm:gap-4 lg:grid-cols-4">
    {% for kpi in kpis %}
        {% component "unfold/components/card.html" with class="h-full" %}
            <div class="flex items-center gap-3">
                <span class="material-symbols-outlined text-primary-500 text-3xl sm:text-4xl shrink-0">{{ kpi.icon }}</span>
                <div class="flex flex-col min-w-0">
                    <span class="text-font-subtle-light dark:text-font-subtle-dark text-xs sm:text-sm">{{ kpi.title }}</span>
                    {% component "unfold/components/title.html" %}{{ kpi.value }}{% endcomponent %}
                </div>
            </div>
        {% endcomponent %}
    {% endfor %}
</div>

{# ---- Charts: visits (line) + devices (doughnut) ---- #}
<div class="grid grid-cols-1 gap-4 mb-8 lg:grid-cols-3">
    <div class="lg:col-span-2">
        {% component "unfold/components/card.html" with title=_('Tashriflar dinamikasi') class="h-full" %}
            <div class="relative w-full" style="height:300px;"><canvas data-dash-chart data-chart="{{ visits_chart }}"></canvas></div>
        {% endcomponent %}
    </div>
    <div>
        {% component "unfold/components/card.html" with title=_('Qurilmalar') class="h-full" %}
            <div class="relative w-full" style="height:200px;"><canvas data-dash-chart data-chart="{{ device_chart }}"></canvas></div>
            {% if device_legend %}
                <div class="mt-5 flex flex-col gap-2.5">
                    {% for d in device_legend %}
                        <div class="flex items-center gap-3">
                            <span class="material-symbols-outlined text-2xl shrink-0" style="color:{{ d.color }}">{{ d.icon }}</span>
                            <span class="text-sm text-font-default-light dark:text-font-default-dark truncate">{{ d.label }}</span>
                            <span class="ml-auto text-sm font-semibold text-font-important-light dark:text-font-important-dark">{{ d.count }}</span>
                            <span class="w-10 text-right text-xs text-font-subtle-light dark:text-font-subtle-dark">{{ d.percent }}%</span>
                        </div>
                    {% endfor %}
                </div>
            {% endif %}
        {% endcomponent %}
    </div>
</div>

{# ---- Leads chart + status ---- #}
<div class="grid grid-cols-1 gap-4 mb-8 lg:grid-cols-3">
    <div class="lg:col-span-2">
        {% component "unfold/components/card.html" with title=_('Arizalar dinamikasi') class="h-full" %}
            <div class="relative w-full" style="height:300px;"><canvas data-dash-chart data-chart="{{ leads_chart }}"></canvas></div>
        {% endcomponent %}
    </div>
    <div>
        {% component "unfold/components/card.html" with title=_('Arizalar holati boʻyicha') class="h-full" %}
            {% component "unfold/components/table.html" with table=leads_by_status %}{% endcomponent %}
        {% endcomponent %}
    </div>
</div>

{# ---- CRM source cards (driven by the global filter) ---- #}
<div class="mb-8">
    {% component "unfold/components/card.html" with title=_('Manbalar boʻyicha lidlar (CRM)') class="h-full" %}
        <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {% for s in source_cards %}
                <div class="flex items-center gap-5 rounded-xl border border-base-200 p-5 dark:border-base-800">
                    <span class="flex h-16 w-16 shrink-0 items-center justify-center overflow-hidden rounded-2xl bg-base-100 dark:bg-base-800" style="{% if s.color %}color:{{ s.color }}{% endif %}">
                        {% if s.image %}<img src="{{ s.image }}" alt="{{ s.name }}" class="h-full w-full rounded-2xl object-cover">
                        {% elif s.brand %}{% social_icon s.brand size=48 %}
                        {% else %}<span class="material-symbols-outlined" style="font-size:48px;line-height:1;">{{ s.icon }}</span>{% endif %}
                    </span>
                    <div class="min-w-0 flex-1">
                        <div class="flex items-center justify-between gap-2">
                            <span class="truncate font-semibold text-base text-font-important-light dark:text-font-important-dark">{{ s.name }}</span>
                            <span class="text-2xl font-bold text-primary-600 dark:text-primary-400">{{ s.count }}</span>
                        </div>
                        <div class="mt-2 h-2 overflow-hidden rounded-full bg-base-100 dark:bg-base-800">
                            <div class="h-full rounded-full bg-primary-500 transition-all" style="width:{{ s.percent }}%"></div>
                        </div>
                        <div class="mt-2 flex items-center justify-between gap-2">
                            <span class="text-xs text-font-subtle-light dark:text-font-subtle-dark">{{ s.percent }}%</span>
                            <button type="button" data-copy-link="{{ s.link }}" class="inline-flex items-center gap-1 text-xs font-medium text-primary-600 hover:text-primary-700 dark:text-primary-400">
                                <span class="material-symbols-outlined text-base">content_copy</span>
                                <span data-copy-label>{% translate "Havola" %}</span>
                            </button>
                        </div>
                    </div>
                </div>
            {% empty %}
                <p class="text-sm text-font-subtle-light dark:text-font-subtle-dark">{% translate "Hali manba yoʻq." %}</p>
            {% endfor %}
        </div>
    {% endcomponent %}
</div>

{# ---- Geo + top tables ---- #}
<div class="grid grid-cols-1 gap-4 lg:grid-cols-2">
    {% component "unfold/components/card.html" with title=_('Davlatlar boʻyicha tashriflar') class="h-full" %}
        {% component "unfold/components/table.html" with table=top_countries %}{% endcomponent %}
    {% endcomponent %}
    {% component "unfold/components/card.html" with title=_('Top sahifalar') class="h-full" %}
        {% component "unfold/components/table.html" with table=top_paths %}{% endcomponent %}
    {% endcomponent %}
    {% component "unfold/components/card.html" with title=_('Top manbalar') class="h-full" %}
        {% component "unfold/components/table.html" with table=top_referrers %}{% endcomponent %}
    {% endcomponent %}
</div>
```

> The `{# ... #}` markers above are each single-line — keep them so.

- [ ] **Step 5: Rewrite `templates/admin/index.html`**

Replace the ENTIRE content block of `templates/admin/index.html` (keep the `{% extends %}`, `{% load %}`, `{% block title %}`, `{% block branding %}` at the top intact) so the `{% block content %}` becomes:

```html
{% block content %}
    {# ---- Global period filter ---- #}
    <div class="flex flex-wrap gap-1.5 mb-6 text-sm" data-dash-tabs data-dash-url="{% url 'admin_dashboard_data' %}" data-active-period="{{ dash_period }}">
        {% for key, label in period_tabs %}
            <a href="?period={{ key }}" data-period="{{ key }}" class="dash-tab px-3.5 py-1.5 rounded-lg font-medium {% if key == dash_period %}bg-primary-600 text-white{% else %}bg-base-100 dark:bg-base-800 text-font-subtle-light dark:text-font-subtle-dark{% endif %}">{{ label }}</a>
        {% endfor %}
    </div>

    <div id="dashboard-content">
        {% include "admin/_dashboard_content.html" %}
    </div>

    {# ---- Static content inventory (not period-filtered) ---- #}
    <div class="grid grid-cols-1 gap-4 mt-8">
        {% component "unfold/components/card.html" with title=_('Sayt kontenti') class="h-full" %}
            {% component "unfold/components/table.html" with table=content_inventory %}{% endcomponent %}
        {% endcomponent %}
    </div>
{% endblock %}
```

The `period_tabs` list is provided by the callback. Add it in `dashboard_callback` (in `dashboard.py`) right before `return context`:

```python
    context["period_tabs"] = [
        ("today", _("Bugun")), ("week", _("Hafta")), ("month", _("Oy")),
        ("year", _("Yil")), ("all", _("Jami")),
    ]
```

Also confirm `templates/admin/index.html` still has `{% load i18n unfold ui %}` at the top (it does after the CRM work).

- [ ] **Step 6: Run tests, verify pass**

Run: `venv/Scripts/python.exe manage.py test apps.analytics.tests.DashboardIndexRenderTests apps.analytics.tests.DashboardDataTests -v 2`
Expected: PASS. Then `venv/Scripts/python.exe manage.py check` → no issues.

> Note: charts show as blank canvases until Task 4 adds the JS — expected. Tables/KPIs/cards render server-side now.

- [ ] **Step 7: Commit**

```bash
git add apps/analytics/dashboard.py templates/admin/index.html templates/admin/_dashboard_content.html apps/analytics/tests.py
git commit -m "feat(dashboard): filter bar + content partial, period-driven server render"
```

---

## Task 3: AJAX endpoint

**Files:**
- Create: `apps/analytics/views.py`
- Modify: `config/urls.py`
- Test: `apps/analytics/tests.py`

**Interfaces:**
- Consumes: `build_dashboard_data`, `clean_period` (Task 1); `_dashboard_content.html` (Task 2).
- Produces: `GET <ADMIN_URL>dashboard-data/?period=X` (name `admin_dashboard_data`) → staff-only; renders the content partial as HTML for the period.

- [ ] **Step 1: Write failing tests**

Add to `apps/analytics/tests.py`:

```python
@override_settings(STORAGES=_STATIC_STORAGE)
class DashboardDataViewTests(TestCase):
    """The AJAX endpoint is staff-only and returns the content partial."""

    def _url(self):
        return reverse("admin_dashboard_data")

    def test_anonymous_is_redirected(self):
        resp = self.client.get(self._url())
        self.assertIn(resp.status_code, (302, 403))

    def test_staff_gets_partial_html(self):
        admin = User.objects.create_superuser(
            username="ajax_admin", password="pass12345", email="a@test.com")
        self.client.force_login(admin)
        resp = self.client.get(self._url() + "?period=week")
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        self.assertIn("data-dash-chart", html)
        self.assertNotIn('data-dash-tabs', html)  # partial only, no filter bar

    def test_invalid_period_defaults_to_month(self):
        admin = User.objects.create_superuser(
            username="ajax_admin2", password="pass12345", email="a2@test.com")
        self.client.force_login(admin)
        resp = self.client.get(self._url() + "?period=bogus")
        self.assertEqual(resp.status_code, 200)
```

- [ ] **Step 2: Run tests, verify they fail**

Run: `venv/Scripts/python.exe manage.py test apps.analytics.tests.DashboardDataViewTests -v 2`
Expected: FAIL — `NoReverseMatch: 'admin_dashboard_data'`.

- [ ] **Step 3: Create the view**

Create `apps/analytics/views.py`:

```python
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

from .dashboard import build_dashboard_data, clean_period


@staff_member_required
def dashboard_data(request):
    """AJAX: render the dashboard content partial for the requested period."""
    period = clean_period(request.GET.get("period"))
    context = build_dashboard_data(request, period)
    return render(request, "admin/_dashboard_content.html", context)
```

- [ ] **Step 4: Wire the URL**

In `config/urls.py`, add the import and the path BEFORE `path(settings.ADMIN_URL, admin.site.urls)` (so the admin catch-all does not swallow it):

```python
from apps.analytics.views import dashboard_data
```

and in `urlpatterns`, immediately after the `app.webmanifest` line:

```python
    path(settings.ADMIN_URL + "dashboard-data/", dashboard_data, name="admin_dashboard_data"),
```

- [ ] **Step 5: Run tests, verify they pass**

Run: `venv/Scripts/python.exe manage.py test apps.analytics.tests.DashboardDataViewTests -v 2`
Expected: PASS (3 tests).

- [ ] **Step 6: Commit**

```bash
git add apps/analytics/views.py config/urls.py apps/analytics/tests.py
git commit -m "feat(dashboard): staff-only AJAX endpoint for period content"
```

---

## Task 4: Admin JS — own charts + point labels + AJAX filter

**Files:**
- Create: `static/js/admin_dashboard.js`
- Modify: `config/settings.py` (`UNFOLD["SCRIPTS"]`)

**Interfaces:**
- Consumes: `[data-dash-chart]` canvases with `data-chart` JSON (Task 1 contract); `[data-dash-tabs]` with `data-dash-url`/`data-active-period`; `#dashboard-content` wrapper; `data-copy-link` buttons (Task 2).
- Produces: client behavior only (no pytest). Verified with `node --check` + manual.

- [ ] **Step 1: Create `static/js/admin_dashboard.js`**

```javascript
// Admin dashboard: own Chart.js instances (so we control granularity, point
// labels and AJAX refresh) + the global period filter. Chart.js is bundled by
// Unfold and available as the global `Chart`.
(function () {
  "use strict";

  function cssColor(key, alpha) {
    var v = getComputedStyle(document.documentElement)
      .getPropertyValue("--color-" + key).trim();
    if (!v) v = "44 107 212";
    var triplet = v.split(/\s+/).join(",");
    return alpha != null ? "rgba(" + triplet + "," + alpha + ")" : "rgb(" + triplet + ")";
  }

  // Draws each point's value above it on line charts; thins labels when dense.
  var pointLabels = {
    id: "pointLabels",
    afterDatasetsDraw: function (chart) {
      if (!chart.$showLabels) return;
      var ctx = chart.ctx;
      chart.data.datasets.forEach(function (ds, di) {
        var meta = chart.getDatasetMeta(di);
        var n = meta.data.length;
        var step = n > 16 ? Math.ceil(n / 12) : 1;
        meta.data.forEach(function (pt, i) {
          if (i % step !== 0 && i !== n - 1) return;
          ctx.save();
          ctx.font = "600 11px Inter, sans-serif";
          ctx.fillStyle = cssColor("primary-600");
          ctx.textAlign = "center";
          ctx.fillText(String(ds.data[i]), pt.x, pt.y - 8);
          ctx.restore();
        });
      });
    },
  };

  function buildChart(canvas, cfg) {
    if (typeof Chart === "undefined") return null;
    var ctx = canvas.getContext("2d");
    if (cfg.type === "doughnut") {
      var ds = cfg.datasets[0] || { data: [], colors: [] };
      return new Chart(ctx, {
        type: "doughnut",
        data: {
          labels: cfg.labels,
          datasets: [{
            data: ds.data,
            backgroundColor: (ds.colors || []).map(function (k) { return cssColor(k); }),
            borderWidth: 0,
          }],
        },
        options: {
          responsive: true, maintainAspectRatio: false, cutout: "62%",
          plugins: { legend: { display: false } },
        },
      });
    }
    // line
    var lds = cfg.datasets[0] || { data: [], line: "primary-500", fill: "primary-100" };
    var chart = new Chart(ctx, {
      type: "line",
      data: {
        labels: cfg.labels,
        datasets: [{
          label: lds.label || "",
          data: lds.data,
          borderColor: cssColor(lds.line || "primary-500"),
          backgroundColor: cssColor(lds.fill || "primary-100", 0.35),
          fill: true, tension: 0.4, pointRadius: 3, borderWidth: 2,
        }],
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        layout: { padding: { top: 18 } },
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true, grid: { color: cssColor("base-200", 0.6) } },
          x: { grid: { display: false } },
        },
      },
      plugins: [pointLabels],
    });
    chart.$showLabels = !!cfg.showLabels;
    return chart;
  }

  window.__dashCharts = window.__dashCharts || [];
  function destroyCharts() {
    window.__dashCharts.forEach(function (c) { try { c.destroy(); } catch (e) {} });
    window.__dashCharts = [];
  }
  function initCharts(root) {
    destroyCharts();
    (root || document).querySelectorAll("[data-dash-chart]").forEach(function (canvas) {
      var cfg;
      try { cfg = JSON.parse(canvas.getAttribute("data-chart")); } catch (e) { return; }
      var chart = buildChart(canvas, cfg);
      if (chart) window.__dashCharts.push(chart);
    });
  }

  function bindCopy(root) {
    (root || document).querySelectorAll("[data-copy-link]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var link = btn.getAttribute("data-copy-link");
        var label = btn.querySelector("[data-copy-label]");
        function flash() {
          if (!label) return;
          var prev = label.textContent;
          label.textContent = "✓";
          setTimeout(function () { label.textContent = prev; }, 1500);
        }
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(link).then(flash).catch(function () {});
        } else {
          var ta = document.createElement("textarea");
          ta.value = link; document.body.appendChild(ta); ta.select();
          try { document.execCommand("copy"); } catch (e) {}
          document.body.removeChild(ta); flash();
        }
      });
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    var tabsBox = document.querySelector("[data-dash-tabs]");
    var content = document.getElementById("dashboard-content");
    if (!tabsBox || !content) return;
    var url = tabsBox.getAttribute("data-dash-url");
    var ACTIVE = ["bg-primary-600", "text-white"];
    var INACTIVE = ["bg-base-100", "dark:bg-base-800", "text-font-subtle-light", "dark:text-font-subtle-dark"];
    var tabs = Array.prototype.slice.call(document.querySelectorAll(".dash-tab"));

    function setActive(period) {
      tabs.forEach(function (t) {
        var on = t.getAttribute("data-period") === period;
        (on ? ACTIVE : INACTIVE).forEach(function (c) { t.classList.add(c); });
        (on ? INACTIVE : ACTIVE).forEach(function (c) { t.classList.remove(c); });
      });
    }

    function load(period) {
      setActive(period);
      content.style.opacity = "0.5";
      fetch(url + "?period=" + encodeURIComponent(period), {
        headers: { "X-Requested-With": "XMLHttpRequest" },
      })
        .then(function (r) { return r.text(); })
        .then(function (html) {
          content.innerHTML = html;
          initCharts(content);
          bindCopy(content);
          try { sessionStorage.setItem("dash_period", period); } catch (e) {}
        })
        .catch(function () {})
        .finally(function () { content.style.opacity = ""; });
    }

    tabs.forEach(function (t) {
      t.addEventListener("click", function (e) {
        e.preventDefault();
        load(t.getAttribute("data-period"));
      });
    });

    // Initial: charts are already server-rendered for the active period. If a
    // different period was saved this session, switch to it.
    initCharts(content);
    bindCopy(content);
    var initial = tabsBox.getAttribute("data-active-period") || "month";
    var saved = null;
    try { saved = sessionStorage.getItem("dash_period"); } catch (e) {}
    if (saved && saved !== initial) load(saved);
  });
})();
```

- [ ] **Step 2: Verify JS syntax**

Run: `node --check static/js/admin_dashboard.js`
Expected: no output, exit 0.

- [ ] **Step 3: Register the script with Unfold**

In `config/settings.py`, in the `UNFOLD` dict, extend the `"SCRIPTS"` list so it reads:

```python
    "SCRIPTS": [
        lambda request: static("js/admin_sidebar.js"),
        lambda request: static("js/admin_dashboard.js"),
    ],
```

- [ ] **Step 4: `manage.py check` + collectstatic sanity**

Run: `venv/Scripts/python.exe manage.py check`
Expected: no issues.

- [ ] **Step 5: Manual verification**

Run: `venv/Scripts/python.exe manage.py runserver 8001`, log into `/admin/`. Confirm:
- The top filter shows **Bugun / Hafta / Oy / Yil / Jami**, with **Oy** active by default.
- Visits & Arizalar charts render with value labels above points; devices doughnut renders.
- Clicking a tab updates ALL widgets (KPIs, charts, tables, device doughnut, CRM cards) with NO page reload; charts re-render.
- Bugun → hourly x-axis; Yil → 12 monthly points; dense periods thin the labels.
- The CRM "Havola" copy button still works. Reloading keeps the last-picked period (sessionStorage).

- [ ] **Step 6: Commit**

```bash
git add static/js/admin_dashboard.js config/settings.py
git commit -m "feat(dashboard): own Chart.js charts + point labels + AJAX period filter"
```

---

## Task 5: Full-suite gate

**Files:** none (verification only)

- [ ] **Step 1: Run the whole suite**

Run: `venv/Scripts/python.exe manage.py test`
Expected: OK, all tests pass (existing + new dashboard tests). If `DashboardSourceCardsTests` (from the earlier CRM work) references removed context keys, update those assertions to read from `build_dashboard_data(...)["source_cards"]` and delete any test asserting the removed per-card `counts_json`/`percents_json` or the old `?source_period` behavior.

- [ ] **Step 2: Commit any test fixups**

```bash
git add apps/analytics/tests.py
git commit -m "test(dashboard): align source-card tests with global filter"
```

---

## Self-Review

**Spec coverage:**
- Top filter Bugun/Hafta/Oy/Yil/Jami, default Oy, sessionStorage → Task 2 (bar) + Task 4 (JS/persist) ✓
- AJAX refresh, no reload → Task 3 (endpoint) + Task 4 (fetch/swap) ✓
- Smart granularity (hour/day/month) → Task 1 `_bucket_keys`/`_series` ✓
- Point labels with thinning → Task 4 `pointLabels` plugin ✓
- Widgets filtered (KPIs, visits, leads, devices+legend, countries, top paths, top referrers, leads-by-status, source cards) → Task 1 `build_dashboard_data` + Task 2 partial ✓
- Static content inventory outside filter → Task 2 (index.html, outside `#dashboard-content`) ✓
- CRM cards lose own tabs, driven by global filter → Task 2 partial (no tabs) ✓
- Own Chart.js (Unfold can't re-init) → Task 4 ✓
- Defensive/error handling → Task 1 (try/except), Task 3 (staff decorator, build_dashboard_data defensive), Task 4 (fetch catch) ✓
- No-JS fallback via `?period=` → Task 2 (anchor tabs + callback reads `?period=`) ✓
- Admin CSS constraint → Global Constraints + partial uses only present classes / inline styles ✓
- Tests → Tasks 1/2/3 + Task 5 gate ✓

**Placeholder scan:** none — every step carries concrete code/commands.

**Type consistency:** `clean_period`, `period_qs`, `_series`, `build_dashboard_data` signatures defined in Task 1 and used identically in Tasks 2/3. Chart JSON contract (`type/labels/datasets/line/fill/colors/showLabels`) defined in Task 1, consumed in Task 4's `buildChart`. Context keys (`dash_period`, `kpis`, `visits_chart`, `leads_chart`, `device_chart`, `device_legend`, `top_paths`, `top_referrers`, `top_countries`, `leads_by_status`, `source_cards`, `period_tabs`, `content_inventory`) consistent between Task 1/2 producers and the partial/template consumers. `data-dash-tabs`/`data-dash-chart`/`data-dash-url`/`#dashboard-content`/`.dash-tab` consistent between Task 2 markup and Task 4 JS.

## Manual QA checklist (after all tasks)
- [ ] `venv/Scripts/python.exe manage.py test` fully green.
- [ ] Filter switches all widgets with no reload; charts animate/re-render.
- [ ] Bugun=hourly, Hafta=7d, Oy=30d, Yil=12mo, Jami=months; labels thin when dense.
- [ ] Icons centered & filling tiles; CRM copy-link works; period persists across reload.
- [ ] No console errors; no missing-CSS layout breaks (Unfold-only utilities).
