from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.analytics.models import VisitLog


class Command(BaseCommand):
    help = "Eski tashrif yozuvlarini oʻchiradi (standart: 6 oydan eski)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--months",
            type=int,
            default=6,
            help="Necha oydan eski yozuvlar oʻchirilsin (standart 6).",
        )

    def handle(self, *args, **options):
        months = options["months"]
        cutoff = timezone.now() - timedelta(days=months * 30)
        deleted, _ = VisitLog.objects.filter(created_at__lt=cutoff).delete()
        self.stdout.write(
            self.style.SUCCESS(
                f"{deleted} ta tashrif yozuvi oʻchirildi "
                f"({months} oydan eski, {cutoff:%Y-%m-%d} dan oldin)."
            )
        )
