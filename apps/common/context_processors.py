from django.conf import settings
from django.core.cache import cache
from django.urls import translate_url

from apps.courses.models import Course
from apps.pages.models import HeroSection, SiteCopy
from apps.siteconfig.models import SiteConfig, SocialLink

# SiteConfig/HeroSection/SiteCopy are already cached by django-solo (SOLO_CACHE).
# social_links and lead_courses aren't singletons, so they don't get that for
# free — every one of them is a query on every public page. A short TTL keeps
# admin edits showing up quickly while cutting the steady-state query count.
CONTEXT_CACHE_TTL = 60  # seconds


def site_context(request):
    """Expose global site config, editable copy, language alternates and course
    list to every template."""
    # The admin renders on every page under ADMIN_URL and needs none of this —
    # skip the queries/URL work entirely there (Unfold has its own context).
    if request.path.startswith("/" + settings.ADMIN_URL.rstrip("/")):
        return {}

    current = request.get_full_path()
    alt_urls = [
        {"code": code, "name": name, "url": translate_url(current, code)}
        for code, name in settings.LANGUAGES
    ]
    social_links = cache.get_or_set(
        "ctx:social_links",
        lambda: list(SocialLink.objects.filter(is_active=True)),
        CONTEXT_CACHE_TTL,
    )
    lead_courses = cache.get_or_set(
        "ctx:lead_courses",
        lambda: list(Course.objects.filter(is_active=True).only("id", "name")),
        CONTEXT_CACHE_TTL,
    )
    return {
        "site_config": SiteConfig.get_solo(),
        "hero_section": HeroSection.get_solo(),
        "site_copy": SiteCopy.get_solo(),
        "social_links": social_links,
        "alt_urls": alt_urls,
        "lead_courses": lead_courses,
        # Ad-link attribution (?source=…): seed the hidden form field server-side
        # so it works with JS off. JS still overwrites it and persists across
        # pages (main.js). Length-capped; junk just resolves to the default source.
        "lead_source_qs": request.GET.get("source", "")[:40],
    }
