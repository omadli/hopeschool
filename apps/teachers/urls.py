from django.urls import path

from .views import TeacherDetailView

app_name = "teachers"

urlpatterns = [
    path("oqituvchilar/<slug:slug>/", TeacherDetailView.as_view(), name="detail"),
]
