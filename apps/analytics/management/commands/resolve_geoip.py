"""Backfill VisitLog.country from IP addresses via ip-api.com.

Run from cron (e.g. every few minutes) or by hand — NEVER in the request path.
Resolves each distinct, still-unresolved public IP once and writes the result
to every row that shares it. Private/loopback IPs are skipped by the resolver
and simply remain blank.

    venv\\Scripts\\python.exe manage.py resolve_geoip
"""
import time

from django.core.management.base import BaseCommand

from apps.analytics.geoip import resolve_ips
from apps.analytics.models import VisitLog

_BATCH = 100


class Command(BaseCommand):
    help = "VisitLog yozuvlariga IP orqali davlat ma'lumotini to'ldiradi (ip-api.com)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit", type=int, default=1000,
            help="Bir martada nechta distinct IP ko'rib chiqilsin (standart 1000).",
        )
        parser.add_argument(
            "--sleep", type=float, default=4.0,
            help="Batchlar orasidagi pauza, sekund (ip-api limiti: ~15 batch/daqiqa).",
        )

    def handle(self, *args, **options):
        # IP fields store NULL (not ""), so isnull is the only emptiness check.
        ips = list(
            VisitLog.objects.filter(country="")
            .exclude(ip_address__isnull=True)
            .values_list("ip_address", flat=True)
            .distinct()[: options["limit"]]
        )
        if not ips:
            self.stdout.write(self.style.SUCCESS("Yangilanadigan IP topilmadi."))
            return

        resolved = 0
        for start in range(0, len(ips), _BATCH):
            chunk = ips[start:start + _BATCH]
            mapping = resolve_ips(chunk)
            for ip, (country, code) in mapping.items():
                if country:
                    VisitLog.objects.filter(ip_address=ip).update(
                        country=country, country_code=code,
                    )
                    resolved += 1
            if start + _BATCH < len(ips):
                time.sleep(options["sleep"])

        self.stdout.write(self.style.SUCCESS(
            f"{resolved} ta IP uchun davlat aniqlandi ({len(ips)} dan ko'rib chiqildi)."
        ))
