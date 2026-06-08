from django.conf import settings
from django.urls import translate_url

from apps.courses.models import Course
from apps.pages.models import HeroSection, SiteCopy
from apps.siteconfig.models import SiteConfig


def site_context(request):
    """Expose global site config, editable copy, language alternates and course
    list to every template."""
    current = request.get_full_path()
    alt_urls = [
        {"code": code, "name": name, "url": translate_url(current, code)}
        for code, name in settings.LANGUAGES
    ]
    return {
        "site_config": SiteConfig.get_solo(),
        "hero_section": HeroSection.get_solo(),
        "site_copy": SiteCopy.get_solo(),
        "alt_urls": alt_urls,
        "lead_courses": Course.objects.filter(is_active=True).only("id", "name"),
    }
