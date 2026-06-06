from django.urls import path

from .views import NewsDetailView, NewsListView

app_name = "news"

urlpatterns = [
    path("yangiliklar/", NewsListView.as_view(), name="list"),
    path("yangiliklar/<slug:slug>/", NewsDetailView.as_view(), name="detail"),
]
