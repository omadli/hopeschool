from django.urls import path

from .views import CertificateListView

app_name = "certificates"

urlpatterns = [
    path("sertifikatlar/", CertificateListView.as_view(), name="list"),
]
