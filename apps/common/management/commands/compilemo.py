"""Compile every ``locale/**/LC_MESSAGES/*.po`` into a ``.mo`` using polib.

A gettext-free replacement for ``manage.py compilemessages``. Django's built-in
command shells out to GNU ``msgfmt``, which is not installed on the Windows dev
box or on this Ubuntu server. The committed ``.po`` files are the source of truth;
this command only compiles them, so it is safe to run on every deploy.

    python manage.py compilemo
"""
from pathlib import Path

import polib
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Compile locale/**/*.po into .mo files using polib (no GNU gettext needed)."

    def handle(self, *args, **options):
        locale_dir = Path(settings.BASE_DIR) / "locale"
        if not locale_dir.is_dir():
            self.stderr.write(f"No locale directory at {locale_dir}")
            return

        count = 0
        for po_path in sorted(locale_dir.rglob("*.po")):
            mo_path = po_path.with_suffix(".mo")
            polib.pofile(str(po_path)).save_as_mofile(str(mo_path))
            count += 1
            self.stdout.write(f"  {po_path.relative_to(locale_dir)} -> {mo_path.name}")

        self.stdout.write(self.style.SUCCESS(f"Compiled {count} catalog(s)."))
