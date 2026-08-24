"""Add VisitLog.visitor_id and backfill it for existing rows.

The dashboard's "users", bounce rate and visit duration are all derived from
this per-day pseudonymous hash, so historic rows are backfilled with the same
formula (IP + UA + SECRET_KEY + the row's local date) rather than left blank —
otherwise every old visit would collapse into a single "user".
"""
import hashlib

from django.conf import settings
from django.db import migrations, models
from django.utils import timezone


def _hash(ip, user_agent, day):
    raw = f"{ip}|{user_agent}|{day.isoformat()}|{settings.SECRET_KEY}"
    return hashlib.sha256(raw.encode("utf-8", "replace")).hexdigest()[:32]


def backfill(apps, schema_editor):
    VisitLog = apps.get_model("analytics", "VisitLog")
    batch = []
    qs = VisitLog.objects.filter(visitor_id="").only(
        "id", "ip_address", "user_agent", "created_at"
    )
    for row in qs.iterator(chunk_size=2000):
        day = timezone.localtime(row.created_at).date()
        row.visitor_id = _hash(row.ip_address or "", row.user_agent or "", day)
        batch.append(row)
        if len(batch) >= 2000:
            VisitLog.objects.bulk_update(batch, ["visitor_id"])
            batch = []
    if batch:
        VisitLog.objects.bulk_update(batch, ["visitor_id"])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("analytics", "0002_visitlog_country_visitlog_country_code"),
    ]

    operations = [
        migrations.AddField(
            model_name="visitlog",
            name="visitor_id",
            field=models.CharField(
                blank=True, db_index=True, max_length=32, verbose_name="Tashrifchi"
            ),
        ),
        migrations.RunPython(backfill, noop),
    ]
