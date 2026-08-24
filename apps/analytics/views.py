from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

from .dashboard import build_dashboard_data
from .geoip import backfill_pending


@staff_member_required
def dashboard_data(request):
    """AJAX: render the dashboard content partial for the requested range."""
    # Opening/refreshing the dashboard is also when we notice countries are
    # still unresolved — kick a capped background backfill (see backfill_pending).
    backfill_pending()
    context = build_dashboard_data(
        request, request.GET.get("period"),
        request.GET.get("from"), request.GET.get("to"),
    )
    return render(request, "admin/_dashboard_content.html", context)
