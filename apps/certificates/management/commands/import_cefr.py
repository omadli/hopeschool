"""Import CEFR certificates from their verification URLs.

For each URL: get-or-create a Certificate (deduped on external_url), download
the PDF, render page 1 to an image and parse the candidate's name + level.
Idempotent — already-imported rows are skipped unless --force.

Usage:
    python manage.py import_cefr                 # bundled student list
    python manage.py import_cefr <url> <url> …   # specific URLs
    python manage.py import_cefr --force         # re-render everything
"""
from django.core.management.base import BaseCommand

from apps.certificates.models import Certificate
from apps.certificates.services import CertificateImportError, populate_certificate

from ._cefr_seed_data import CEFR_CERTIFICATE_URLS


class Command(BaseCommand):
    help = "Import CEFR certificates from verification URLs (PDF -> image + name)."

    def add_arguments(self, parser):
        parser.add_argument(
            "urls", nargs="*",
            help="Certificate URLs (default: bundled student list).",
        )
        parser.add_argument(
            "--force", action="store_true",
            help="Re-download and re-render even if an image already exists.",
        )

    def handle(self, *args, **options):
        urls = options["urls"] or CEFR_CERTIFICATE_URLS
        created = updated = skipped = failed = 0

        for i, url in enumerate(urls):
            cert, was_created = Certificate.objects.get_or_create(
                external_url=url,
                defaults={"title": "CEFR sertifikati", "is_active": True, "order": i},
            )
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
