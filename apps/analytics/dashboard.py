"""Unfold dashboard callback for the admin index page.

Wired via UNFOLD["DASHBOARD_CALLBACK"]. Unfold calls this as
``context = dashboard_callback(request, context)`` (sites.py), so it MUST
return the context. The whole body is defensive: if the analytics table does
not yet exist (e.g. during a migration window) it degrades to zeros instead of
500-ing the admin index.
"""
import json
from datetime import timedelta

from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

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
        }],
    })

    # ---- Device-type breakdown -------------------------------------------
    device_rows = (
        visits.values("device_type").annotate(total=Count("id")).order_by("-total")
    )
    device_labels = [str(_DEVICE_LABELS.get(r["device_type"], r["device_type"])) for r in device_rows]
    device_data = [r["total"] for r in device_rows]
    context["device_chart"] = json.dumps({
        "labels": device_labels,
        "datasets": [{
            "label": str(_("Qurilmalar")),
            "data": device_data,
            "backgroundColor": _DEVICE_COLORS[: len(device_data)] or _DEVICE_COLORS,
        }],
    })

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

    return context


def dashboard_callback(request, context):
    try:
        return _build_context(request, context)
    except Exception:
        # Degrade gracefully (e.g. table not yet migrated) — keep admin alive.
        context.setdefault("kpis", [])
        context.setdefault("visits_chart", _empty_chart())
        context.setdefault("device_chart", _empty_chart())
        context.setdefault("top_paths", {"headers": [], "rows": []})
        context.setdefault("top_referrers", {"headers": [], "rows": []})
        return context
