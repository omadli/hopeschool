from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),  # set_language (outside i18n_patterns)
    path("ckeditor5/", include("django_ckeditor_5.urls")),
]

urlpatterns += i18n_patterns(
    path("", include("apps.pages.urls")),
    path("", include("apps.courses.urls")),
    path("", include("apps.teachers.urls")),
    path("", include("apps.gallery.urls")),
    path("", include("apps.news.urls")),
    path("", include("apps.certificates.urls")),
    prefix_default_language=True,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
