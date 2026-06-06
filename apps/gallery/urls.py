from django.urls import path

from .views import GalleryListView

app_name = "gallery"

urlpatterns = [
    path("galereya/", GalleryListView.as_view(), name="list"),
]
