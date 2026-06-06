from django.apps import AppConfig


class LeadsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.leads"
    verbose_name = "Murojaatlar"

    def ready(self):
        # Connect post_save -> Telegram notification signal.
        from . import signals  # noqa: F401
