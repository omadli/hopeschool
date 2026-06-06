from django.urls import path

from .views import CourseDetailView

app_name = "courses"

urlpatterns = [
    path("kurslar/<slug:slug>/", CourseDetailView.as_view(), name="detail"),
]
