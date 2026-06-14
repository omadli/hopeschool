"""Project-wide middleware."""
from django.conf import settings
from django.middleware.locale import LocaleMiddleware


class DefaultUzLocaleMiddleware(LocaleMiddleware):
    """LocaleMiddleware that keeps the public site default language at uz.

    The browser Accept-Language header is never used. On the public site the
    language comes purely from the URL prefix (the switcher links to /uz//ru//en/),
    so a leftover django_language cookie must not override the uz default either.
    The admin keeps cookie-based language selection (its URLs are not prefixed)."""

    def process_request(self, request):
        request.META.pop("HTTP_ACCEPT_LANGUAGE", None)
        if not request.path.startswith("/" + settings.ADMIN_URL):
            request.COOKIES.pop(settings.LANGUAGE_COOKIE_NAME, None)
        super().process_request(request)
