from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

from .dashboard import build_dashboard_data, clean_period


@staff_member_required
def dashboard_data(request):
    """AJAX: render the dashboard content partial for the requested period."""
    period = clean_period(request.GET.get("period"))
    context = build_dashboard_data(request, period)
    return render(request, "admin/_dashboard_content.html", context)
