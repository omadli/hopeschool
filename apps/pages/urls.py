from django.urls import path
from django.views.generic import TemplateView

from .views import LandingView

urlpatterns = [
    path("", LandingView.as_view(), name="home"),
    path("maxfiylik/", TemplateView.as_view(template_name="pages/privacy.html"),
         name="privacy"),
]
