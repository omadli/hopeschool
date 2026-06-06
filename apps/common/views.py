"""Common public views (robots.txt, etc.)."""
from django.http import HttpResponse
from django.urls import reverse
from django.views.decorators.http import require_GET


@require_GET
def robots_txt(request):
    """Serve robots.txt with an absolute Sitemap URL built from the request."""
    sitemap_url = request.build_absolute_uri(reverse("django.contrib.sitemaps.views.sitemap"))
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "Disallow: /i18n/",
        "Disallow: /ckeditor5/",
        f"Sitemap: {sitemap_url}",
    ]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain")
