from django.views.generic import ListView

from .models import Certificate


class CertificateListView(ListView):
    template_name = "certificates/list.html"
    context_object_name = "certificates"
    paginate_by = 24

    def get_queryset(self):
        return Certificate.objects.filter(is_active=True)
