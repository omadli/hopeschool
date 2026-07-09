"""Import CEFR certificates from their verification URLs.

URLs come from (in priority order):
  1. positional arguments, or
  2. ``--file PATH`` (one URL per line; blank lines and ``#`` comments ignored), or
  3. the default ``cefr_urls.txt`` in the project root.

The URL list holds real student data, so it is kept OUT of the repo (gitignored
``cefr_urls.txt``) — never hard-coded here.

For each URL: get-or-create a Certificate (deduped on external_url), download
the PDF, render page 1 to an image and parse the candidate's name + level.
Idempotent — already-imported rows are skipped unless --force.

Usage:
    python manage.py import_cefr                  # reads cefr_urls.txt
    python manage.py import_cefr --file urls.txt  # reads a specific file
    python manage.py import_cefr <url> <url> …    # explicit URLs
    python manage.py import_cefr --force          # re-render everything
    python manage.py import_cefr --reorder        # just renumber `order`
                                                   # (chronological by issued_on,
                                                   # repeat-certificate students
                                                   # grouped together)
"""
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import models

from apps.certificates.models import Certificate
from apps.certificates.services import (
    CertificateImportError,
    populate_certificate,
    reorder_certificates,
)

DEFAULT_URL_FILE = "cefr_urls.txt"


def _read_url_file(path):
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    urls = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith("#"):
            urls.append(line)
    return urls


class Command(BaseCommand):
    help = "Import CEFR certificates from verification URLs (PDF -> image + name)."

    def add_arguments(self, parser):
        parser.add_argument(
            "urls", nargs="*",
            help="Certificate URLs. If omitted, reads --file or cefr_urls.txt.",
        )
        parser.add_argument(
            "--file", dest="file",
            help="Path to a newline-delimited URL file (# comments allowed).",
        )
        parser.add_argument(
            "--force", action="store_true",
            help="Re-download and re-render even if an image already exists.",
        )
        parser.add_argument(
            "--reorder", action="store_true",
            help="Renumber `order` chronologically by issued_on afterward "
                 "(or on its own, with no URLs, to just reorder existing rows).",
        )

    def _resolve_urls(self, options):
        if options["urls"]:
            return options["urls"]
        path = options["file"] or (Path(settings.BASE_DIR) / DEFAULT_URL_FILE)
        if not Path(path).exists():
            raise CommandError(
                f"URL manbasi topilmadi. URL'larni argument sifatida bering, "
                f"--file ko'rsating yoki '{DEFAULT_URL_FILE}' faylini yarating."
            )
        urls = _read_url_file(path)
        if not urls:
            raise CommandError(f"'{path}' faylida URL topilmadi.")
        return urls

    def handle(self, *args, **options):
        reorder_only = options["reorder"] and not options["urls"] and not options["file"]
        if reorder_only:
            changed = reorder_certificates()
            self.stdout.write(self.style.SUCCESS(f"Qayta tartiblandi — {changed} ta yozuv."))
            return

        urls = self._resolve_urls(options)
        created = updated = skipped = failed = 0
        next_order = (
            Certificate.objects.aggregate(models.Max("order"))["order__max"] or -1
        ) + 1

        for url in urls:
            cert, was_created = Certificate.objects.get_or_create(
                external_url=url,
                defaults={"title": "CEFR sertifikati", "is_active": True, "order": next_order},
            )
            if was_created:
                next_order += 1
            if cert.image and not options["force"]:
                self.stdout.write(f"=  skip (mavjud): {url}")
                skipped += 1
                continue
            try:
                data = populate_certificate(cert, save=True)
            except CertificateImportError as exc:
                self.stderr.write(self.style.ERROR(f"x  XATO {url}: {exc}"))
                failed += 1
                continue

            name = data.get("name") or "(ism aniqlanmadi — qoʻlda kiriting)"
            tag = "+  yangi" if was_created else "~  yangilandi"
            self.stdout.write(f"{tag}: {name}  [{data.get('level') or '?'}]")
            created += int(was_created)
            updated += int(not was_created)

        self.stdout.write(self.style.SUCCESS(
            f"Tayyor — yangi: {created}, yangilangan: {updated}, "
            f"oʻtkazib yuborilgan: {skipped}, xato: {failed}"
        ))

        if options["reorder"]:
            changed = reorder_certificates()
            self.stdout.write(self.style.SUCCESS(f"Qayta tartiblandi — {changed} ta yozuv."))
