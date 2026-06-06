from django.urls import path

from .views import lead_create

app_name = "leads"

urlpatterns = [
    path("ariza/", lead_create, name="lead_create"),
]
