"""Project-wide middleware."""
from django.middleware.locale import LocaleMiddleware


class DefaultUzLocaleMiddleware(LocaleMiddleware):
    """LocaleMiddleware that ignores the browser Accept-Language header so the
    default language is always uz. Only a language-prefixed URL or the
    django_language cookie (set by the switcher) may select another language."""

    def process_request(self, request):
        request.META.pop("HTTP_ACCEPT_LANGUAGE", None)
        super().process_request(request)
