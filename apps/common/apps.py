from django.apps import AppConfig
from django.contrib.staticfiles.apps import StaticFilesConfig


class CommonConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.common"
    verbose_name = "Umumiy"


class CustomStaticFilesConfig(StaticFilesConfig):
    """Drop-in replacement for ``django.contrib.staticfiles`` that excludes the
    Tailwind source CSS from ``collectstatic``.

    ``assets/css/source.css`` lives inside a ``STATICFILES_DIRS`` directory so the
    Tailwind CLI can resolve its ``@source`` paths, but it must never be collected:
    its ``@import "tailwindcss";`` line makes WhiteNoise's manifest storage try to
    resolve a non-existent ``css/tailwindcss`` and abort ``collectstatic``. Only the
    compiled ``assets/css/tailwind.css`` should ship. ``ignore_patterns`` match the
    basename, so ``"source.css"`` (not ``"css/source.css"``) is correct.
    """

    ignore_patterns = [*StaticFilesConfig.ignore_patterns, "source.css"]
