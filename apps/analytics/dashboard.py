"""Unfold dashboard callback for the admin index page.

Wired via UNFOLD["DASHBOARD_CALLBACK"]. Unfold calls this as
``context = dashboard_callback(request, context)`` (sites.py), so it MUST
return the context. The whole body is defensive: if the analytics table does
not yet exist (e.g. during a migration window) it degrades to zeros instead of
500-ing the admin index.
"""
import json
from datetime import timedelta

from django.db.models import Count, Min
from django.db.models.functions import TruncDate, TruncHour, TruncMonth
from django.utils import timezone
from django.utils.translation import get_language, gettext_lazy as _

from .models import VisitLog

_DEVICE_LABELS = dict(VisitLog.DeviceType.choices)

# Material Symbols icon per device type (shown in the doughnut legend).
_DEVICE_ICONS = {
    "mobile": "smartphone",
    "tablet": "tablet",
    "desktop": "computer",
    "bot": "smart_toy",
    "other": "devices_other",
}


PERIODS = ("today", "week", "month", "year", "all")
DEFAULT_PERIOD = "month"

# Doughnut/legend colours as Unfold CSS-variable *keys* (resolved to rgb in JS
# for the canvas; the legend HTML wraps each in var(--color-<key>)).
_DEVICE_COLOR_KEYS = ["primary-500", "primary-300", "primary-700", "base-400", "base-300"]


def clean_period(value):
    """Whitelist a requested period, defaulting to month."""
    return value if value in PERIODS else DEFAULT_PERIOD


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


def _period_start_date(period, today):
    """Calendar start date matching the chart bucket windows (None = no lower
    bound), so KPIs/tables reconcile with the chart bars."""
    if period == "week":
        return today - timedelta(days=6)
    if period == "month":
        return today - timedelta(days=29)
    if period == "year":
        return _month_range(_month_first(today), 12)[0]
    return None


def period_qs(qs, period, now, today):
    """Filter a queryset to the period's window (aligned to the chart buckets)."""
    if period == "today":
        return qs.filter(created_at__date=today)
    start = _period_start_date(period, today)
    if start is None:
        return qs  # all
    return qs.filter(created_at__date__gte=start)


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
    if not keys_labels:
        return labels, []
    if gran == "day":
        first = keys_labels[0][0]
        rows = (qs.filter(created_at__date__gte=first)
                  .annotate(b=TruncDate("created_at")).values("b").annotate(t=Count("id")))
        counts = {r["b"]: r["t"] for r in rows}
        return labels, [counts.get(d, 0) for d, _l in keys_labels]
    first = keys_labels[0][0]
    rows = (qs.filter(created_at__date__gte=first)
              .annotate(b=TruncMonth("created_at")).values("b").annotate(t=Count("id")))
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
    context["period_tabs"] = [
        ("today", _("Bugun")), ("week", _("Hafta")), ("month", _("Oy")),
        ("year", _("Yil")), ("all", _("Jami")),
    ]
    return context


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
        for k in ("visits_chart", "leads_chart"):
            data.setdefault(k, json.dumps({"type": "line", "labels": [], "datasets": []}))
        data.setdefault("device_chart", json.dumps({"type": "doughnut", "labels": [], "datasets": []}))
        data.setdefault("device_legend", [])
        for k in ("top_paths", "top_referrers", "top_countries", "leads_by_status"):
            data.setdefault(k, {"headers": [], "rows": []})
        data.setdefault("source_cards", [])
    return data
