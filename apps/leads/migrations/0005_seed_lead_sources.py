from django.db import migrations

BUILTINS = [
    {"slug": "site", "name": "Sayt", "icon": "public", "order": 0},
    {"slug": "telegram", "name": "Telegram", "icon": "send", "order": 1},
    {"slug": "instagram", "name": "Instagram", "icon": "photo_camera", "order": 2},
    {"slug": "facebook", "name": "Facebook", "icon": "thumb_up", "order": 3},
]


def seed_sources(apps, schema_editor):
    LeadSource = apps.get_model("leads", "LeadSource")
    Lead = apps.get_model("leads", "Lead")
    site = None
    for row in BUILTINS:
        obj, _created = LeadSource.objects.get_or_create(
            slug=row["slug"],
            defaults={
                "name": row["name"], "icon": row["icon"],
                "order": row["order"], "is_protected": True,
            },
        )
        if row["slug"] == "site":
            site = obj
    # Existing leads all came through the website form.
    Lead.objects.filter(source__isnull=True).update(source=site)


def unseed_sources(apps, schema_editor):
    LeadSource = apps.get_model("leads", "LeadSource")
    LeadSource.objects.filter(
        slug__in=[b["slug"] for b in BUILTINS]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("leads", "0004_lead_source_referrer"),
    ]

    operations = [
        migrations.RunPython(seed_sources, unseed_sources),
    ]
