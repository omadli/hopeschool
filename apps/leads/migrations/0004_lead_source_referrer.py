from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("leads", "0003_leadsource"),
    ]

    operations = [
        migrations.RenameField(
            model_name="lead",
            old_name="source",
            new_name="referrer",
        ),
        migrations.AlterField(
            model_name="lead",
            name="referrer",
            field=models.CharField(
                blank=True,
                max_length=255,
                verbose_name="Referrer",
                help_text="UTM yoki referrer (avtomatik toʻldiriladi).",
            ),
        ),
        migrations.AddField(
            model_name="lead",
            name="source",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="leads",
                to="leads.leadsource",
                verbose_name="Manba",
            ),
        ),
    ]
