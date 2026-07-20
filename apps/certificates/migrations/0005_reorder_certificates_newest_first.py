"""Re-apply certificate `order` newest-first (see services.reorder_certificates).

The old ordering numbered oldest→newest; this renumbers existing rows so the
newest certificates appear first. Order-only data change, reversible as a no-op
(the next import re-runs reorder anyway).
"""
from django.db import migrations


def apply_newest_first(apps, schema_editor):
    # reorder_certificates only reads student_name/issued_on/id and writes
    # `order` — all stable fields — so calling the service here is safe.
    from apps.certificates.services import reorder_certificates
    reorder_certificates()


class Migration(migrations.Migration):

    dependencies = [
        ("certificates", "0004_remove_certificate_badge_en_and_more"),
    ]

    operations = [
        migrations.RunPython(apply_newest_first, migrations.RunPython.noop),
    ]
