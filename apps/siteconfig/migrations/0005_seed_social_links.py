"""Copy the existing fixed SiteConfig social URLs into SocialLink rows.

Runs BEFORE the SiteConfig social fields are removed (migration 0006), so no
configured link is lost when the fixed fields give way to the repeatable model.
"""
from django.db import migrations

# (SocialLink.platform, SiteConfig field name)
SOCIAL_FIELDS = [
    ("instagram", "instagram_url"),
    ("telegram", "telegram_url"),
    ("telegram_group", "telegram_group_url"),
    ("youtube", "youtube_url"),
    ("facebook", "facebook_url"),
    ("tiktok", "tiktok_url"),
]


def seed_social(apps, schema_editor):
    SiteConfig = apps.get_model("siteconfig", "SiteConfig")
    SocialLink = apps.get_model("siteconfig", "SocialLink")
    cfg = SiteConfig.objects.first()
    if cfg is None:
        return
    order = 0
    for platform, field in SOCIAL_FIELDS:
        url = (getattr(cfg, field, "") or "").strip()
        if url and not SocialLink.objects.filter(url=url).exists():
            SocialLink.objects.create(
                platform=platform, url=url, order=order, is_active=True,
            )
            order += 1


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("siteconfig", "0004_sociallink"),
    ]
    operations = [
        migrations.RunPython(seed_social, noop),
    ]
