from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from apps.common.sitemaps import sitemaps
from apps.common.views import robots_txt, web_manifest
from apps.leads.views import lead_create

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),  # set_language (outside i18n_patterns)
    path("ckeditor5/", include("django_ckeditor_5.urls")),
    path("ariza/", lead_create, name="lead_create"),  # lead submit (no lang prefix)

    # SEO (outside i18n_patterns: single canonical, no language prefix)
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps},
         name="django.contrib.sitemaps.views.sitemap"),
    path("robots.txt", robots_txt, name="robots_txt"),
    path("site.webmanifest", web_manifest, name="web_manifest"),
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
