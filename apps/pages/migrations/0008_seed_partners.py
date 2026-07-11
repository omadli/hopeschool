"""Seed the 7 partner names that were previously hardcoded in
templates/sections/_partners.html, so the marquee isn't empty on first deploy.
website_url is left blank — an admin can fill it in later per partner.
"""
from django.db import migrations

PARTNERS = [
    "Cambridge", "IELTS", "Pearson", "Khan Academy", "Coursera", "Oxford",
    "British Council",
]


def seed_partners(apps, schema_editor):
    Partner = apps.get_model("pages", "Partner")
    if Partner.objects.exists():
        return
    for i, name in enumerate(PARTNERS):
        Partner.objects.create(
            order=i, is_active=True,
            name=name, name_uz=name, name_ru=name, name_en=name,
            website_url="",
        )


def noop(apps, schema_editor):
    # Data-only seed; nothing to undo (leaving the rows is harmless).
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("pages", "0007_partner"),
    ]

    operations = [
        migrations.RunPython(seed_partners, noop),
    ]
