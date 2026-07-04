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

# Tailwind/Unfold CSS variables understood by the chart JS colour resolver.
_LINE_COLOR = "var(--color-primary-500)"
_FILL_COLOR = "var(--color-primary-100)"
_DEVICE_COLORS = [
    "var(--color-primary-500)",
    "var(--color-primary-300)",
    "var(--color-primary-700)",
    "var(--color-base-400)",
    "var(--color-base-300)",
]

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


def _empty_chart():
    return json.dumps({"labels": [], "datasets": []})


def _build_context(request, context):
    now = timezone.now()
    today = timezone.localdate()
    last_30 = now - timedelta(days=30)

    visits = VisitLog.objects.all()

    # ---- KPIs -------------------------------------------------------------
    visits_today = visits.filter(created_at__date=today).count()
    visits_30 = visits.filter(created_at__gte=last_30).count()
    visits_total = visits.count()

    # Leads (imported lazily so analytics has no hard import dependency).
    from apps.leads.models import Lead

    leads = Lead.objects.all()
    new_leads = leads.filter(status=Lead.Status.NEW).count()
    leads_30 = leads.filter(created_at__gte=last_30).count()

    from apps.courses.models import Course
    from apps.teachers.models import Teacher

    courses_total = Course.objects.count()
    teachers_total = Teacher.objects.count()

    context["kpis"] = [
        {"title": _("Bugungi tashriflar"), "value": visits_today, "icon": "today"},
        {"title": _("Tashriflar (30 kun)"), "value": visits_30, "icon": "trending_up"},
        {"title": _("Jami tashriflar"), "value": visits_total, "icon": "visibility"},
        {"title": _("Yangi arizalar"), "value": new_leads, "icon": "inbox"},
        {"title": _("Arizalar (30 kun)"), "value": leads_30, "icon": "mail"},
        {"title": _("Kurslar / oʻqituvchilar"),
         "value": f"{courses_total} / {teachers_total}", "icon": "school"},
    ]

    # ---- Visits per day, last 14 days (gap-filled) ------------------------
    span_start = today - timedelta(days=13)
    per_day = (
        visits.filter(created_at__date__gte=span_start)
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(total=Count("id"))
    )
    counts_by_day = {row["day"]: row["total"] for row in per_day}
    labels, series = [], []
    for offset in range(14):
        day = span_start + timedelta(days=offset)
        labels.append(day.strftime("%d.%m"))
        series.append(counts_by_day.get(day, 0))

    context["visits_chart"] = json.dumps({
        "labels": labels,
        "datasets": [{
            "label": str(_("Tashriflar")),
            "data": series,
            "borderColor": _LINE_COLOR,
            "backgroundColor": _FILL_COLOR,
            "fill": True,
            "tension": 0.4,
            # Show the count scale on the Y axis (day-by-day totals are then
            # readable; hovering a point still shows the exact number).
            "displayYAxis": True,
        }],
    })

    # ---- Device-type breakdown -------------------------------------------
    device_rows = list(
        visits.values("device_type").annotate(total=Count("id")).order_by("-total")
    )
    device_labels = [str(_DEVICE_LABELS.get(r["device_type"], r["device_type"])) for r in device_rows]
    device_data = [r["total"] for r in device_rows]
    device_colors = _DEVICE_COLORS[: len(device_data)] or _DEVICE_COLORS
    context["device_chart"] = json.dumps({
        "labels": device_labels,
        "datasets": [{
            "label": str(_("Qurilmalar")),
            "data": device_data,
            "backgroundColor": device_colors,
        }],
    })
    # Custom legend rendered under the doughnut: icon + label + count + share.
    device_total = sum(device_data) or 1
    context["device_legend"] = [
        {
            "label": device_labels[i],
            "count": row["total"],
            "percent": round(row["total"] * 100 / device_total),
            "color": device_colors[i % len(device_colors)],
            "icon": _DEVICE_ICONS.get(row["device_type"], "devices_other"),
        }
        for i, row in enumerate(device_rows)
    ]

    # ---- Top 5 paths ------------------------------------------------------
    top_paths = list(
        visits.values("path").annotate(total=Count("id")).order_by("-total")[:5]
    )
    context["top_paths"] = {
        "headers": [str(_("Sahifa")), str(_("Tashriflar"))],
        "rows": [[p["path"], p["total"]] for p in top_paths],
    }

    # ---- Top 5 referrers --------------------------------------------------
    top_referrers = list(
        visits.exclude(referrer="")
        .values("referrer")
        .annotate(total=Count("id"))
        .order_by("-total")[:5]
    )
    context["top_referrers"] = {
        "headers": [str(_("Manba")), str(_("Tashriflar"))],
        "rows": [[r["referrer"], r["total"]] for r in top_referrers],
    }

    # ---- Leads per day, last 14 days (gap-filled) -------------------------
    leads_per_day = (
        leads.filter(created_at__date__gte=span_start)
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(total=Count("id"))
    )
    leads_by_day = {row["day"]: row["total"] for row in leads_per_day}
    lead_series = [leads_by_day.get(span_start + timedelta(days=o), 0) for o in range(14)]
    context["leads_chart"] = json.dumps({
        "labels": labels,
        "datasets": [{
            "label": str(_("Arizalar")),
            "data": lead_series,
            "borderColor": "var(--color-primary-600)",
            "backgroundColor": _FILL_COLOR,
            "fill": True,
            "tension": 0.4,
        }],
    })

    # ---- Leads by status --------------------------------------------------
    status_labels = dict(Lead.Status.choices)
    status_rows = leads.values("status").annotate(total=Count("id")).order_by("-total")
    context["leads_by_status"] = {
        "headers": [str(_("Holat")), str(_("Soni"))],
        "rows": [[str(status_labels.get(r["status"], r["status"])), r["total"]]
                 for r in status_rows],
    }

    # ---- Top countries (resolved by resolve_geoip) ------------------------
    country_rows = (
        visits.exclude(country="")
        .values("country")
        .annotate(total=Count("id"))
        .order_by("-total")[:8]
    )
    context["top_countries"] = {
        "headers": [str(_("Davlat")), str(_("Tashriflar"))],
        "rows": [[r["country"], r["total"]] for r in country_rows],
    }

    # ---- Content inventory (totals + active/published) --------------------
    from apps.certificates.models import Certificate
    from apps.gallery.models import GalleryImage
    from apps.news.models import NewsPost
    from apps.testimonials.models import Testimonial

    inventory = [
        (_("Kurslar"), Course.objects, {"is_active": True}),
        (_("Oʻqituvchilar"), Teacher.objects, {"is_active": True}),
        (_("Yangiliklar"), NewsPost.objects, {"is_published": True}),
        (_("Sertifikatlar"), Certificate.objects, {"is_active": True}),
        (_("Fikrlar"), Testimonial.objects, {"is_active": True}),
        (_("Galereya rasmlari"), GalleryImage.objects, {"is_active": True}),
    ]
    context["content_inventory"] = {
        "headers": [str(_("Boʻlim")), str(_("Jami")), str(_("Faol / chop etilgan"))],
        "rows": [[str(label), mgr.count(), mgr.filter(**flt).count()]
                 for label, mgr, flt in inventory],
    }

    # ---- CRM: leads per source, all periods (switched inline by JS) --------
    from django.utils.translation import get_language

    from apps.leads.models import LeadSource
    from apps.siteconfig.models import SiteConfig

    # Rolling windows; keys match the dashboard tabs and the JS switcher. All
    # periods are computed up front so the tabs switch client-side with no page
    # reload and no extra request (the dataset is tiny — a few sources).
    week_start = now - timedelta(days=7)
    period_qs = {
        "today": leads.filter(created_at__date=today),
        "week": leads.filter(created_at__gte=week_start),
        "30": leads.filter(created_at__gte=last_30),
        "all": leads,
    }
    active_sources = list(LeadSource.objects.filter(is_active=True))
    active_ids = [s.id for s in active_sources]

    # Per-period counts keyed by source id, plus the per-period denominator —
    # summed over only the shown active sources, so displayed shares total ~100
    # even when some leads belong to an inactive/deleted (NULL) source.
    period_counts, period_total = {}, {}
    for key, qs in period_qs.items():
        c = {row["source"]: row["total"]
             for row in qs.values("source").annotate(total=Count("id"))}
        period_counts[key] = c
        period_total[key] = sum(c.get(sid, 0) for sid in active_ids) or 1

    try:
        domain = SiteConfig.get_solo().site_domain or request.get_host()
    except Exception:  # pragma: no cover - defensive
        domain = request.get_host()
    lang = get_language() or "uz"

    default_period = "all"  # tab shown first (also the no-JS fallback value)
    source_cards = []
    # Fixed admin order (OrderedActiveModel) — cards do not reshuffle on switch.
    for s in active_sources:
        counts = {k: period_counts[k].get(s.id, 0) for k in period_qs}
        percents = {k: round(counts[k] * 100 / period_total[k]) for k in period_qs}
        source_cards.append({
            "name": s.name,
            "link": s.build_link(domain, lang),
            "image": s.image.url if s.image else "",
            "brand": s.brand_key,
            "icon": s.icon or "hub",
            "color": s.color or "",
            "counts_json": json.dumps(counts),
            "percents_json": json.dumps(percents),
            "count": counts[default_period],
            "percent": percents[default_period],
        })
    context["source_cards"] = source_cards
    context["source_period"] = default_period

    return context


def dashboard_callback(request, context):
    try:
        return _build_context(request, context)
    except Exception:
        # Degrade gracefully (e.g. table not yet migrated) — keep admin alive.
        context.setdefault("kpis", [])
        context.setdefault("visits_chart", _empty_chart())
        context.setdefault("device_chart", _empty_chart())
        context.setdefault("device_legend", [])
        context.setdefault("leads_chart", _empty_chart())
        context.setdefault("top_paths", {"headers": [], "rows": []})
        context.setdefault("top_referrers", {"headers": [], "rows": []})
        context.setdefault("leads_by_status", {"headers": [], "rows": []})
        context.setdefault("top_countries", {"headers": [], "rows": []})
        context.setdefault("content_inventory", {"headers": [], "rows": []})
        context.setdefault("source_cards", [])
        context.setdefault("source_period", "all")
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
        for k in ("visits_chart", "leads_chart", "device_chart"):
            data.setdefault(k, json.dumps({"type": "line", "labels": [], "datasets": []}))
        data.setdefault("device_legend", [])
        for k in ("top_paths", "top_referrers", "top_countries", "leads_by_status"):
            data.setdefault(k, {"headers": [], "rows": []})
        data.setdefault("source_cards", [])
    return data
