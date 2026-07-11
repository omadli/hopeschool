"""Move the hero poster's storage location to where it actually belongs.

HeroSection had no image field, so whoever set up the site uploaded the hero
poster through AboutSection ("Biz haqimizda bo'limi") instead — a section
that has nothing to do with the hero block. That's the file the homepage's
hero image tag has been reading via `about.image`. Now that HeroSection has
its own `image` field, copy the current file across so production doesn't
go blank on deploy; AboutSection.image is left as-is (still a valid, unused
field for a future "About us" photo).
"""
from django.db import migrations


def copy_image(apps, schema_editor):
    AboutSection = apps.get_model("pages", "AboutSection")
    HeroSection = apps.get_model("pages", "HeroSection")
    about = AboutSection.objects.filter(is_active=True).order_by("order").first()
    if not about or not about.image:
        return
    hero = HeroSection.objects.first()
    if hero and not hero.image:
        hero.image = about.image
        hero.save(update_fields=["image"])


def noop(apps, schema_editor):
    # Data-only copy; nothing to undo (leaving the copy is harmless).
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("pages", "0009_herosection_image"),
    ]

    operations = [
        migrations.RunPython(copy_image, noop),
    ]
