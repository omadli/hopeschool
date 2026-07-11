from django.db.models import Count
from django.db.models.functions import ExtractYear
from django.views.generic import ListView

from .models import Certificate


class CertificateListView(ListView):
    template_name = "certificates/list.html"
    context_object_name = "certificates"
    paginate_by = 25

    def get_queryset(self):
        qs = Certificate.objects.filter(is_active=True)
        self.selected_year = self.request.GET.get("year", "")
        if self.selected_year.isdigit():
            qs = qs.filter(issued_on__year=self.selected_year)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["years"] = (
            Certificate.objects.filter(is_active=True, issued_on__isnull=False)
            .annotate(year=ExtractYear("issued_on"))
            .values("year")
            .annotate(count=Count("id"))
            .order_by("-year")
        )
        ctx["selected_year"] = self.selected_year
        return ctx
