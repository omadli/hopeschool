"""Common public views (robots.txt, web manifest, etc.)."""
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_GET


@require_GET
def robots_txt(request):
    """Serve robots.txt with an absolute Sitemap URL built from the request."""
    sitemap_url = request.build_absolute_uri(reverse("django.contrib.sitemaps.views.sitemap"))
    lines = [
        "User-agent: *",
        "Allow: /",
        # NOTE: the real admin lives at the obfuscated settings.ADMIN_URL, which
        # we deliberately do NOT publish here. Blocking the default /admin/ path
        # keeps naive crawlers off the login guess without leaking the real one.
        "Disallow: /admin/",
        "Disallow: /i18n/",
        "Disallow: /ckeditor5/",
        "Disallow: /ariza/",  # POST-only lead endpoint, nothing to index
        f"Sitemap: {sitemap_url}",
    ]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain")


@require_GET
def web_manifest(request):
    """Serve the PWA web app manifest (rendered so {% static %} resolves hashed
    asset URLs and the correct application/manifest+json content type is set)."""
    return render(request, "site.webmanifest", content_type="application/manifest+json")
