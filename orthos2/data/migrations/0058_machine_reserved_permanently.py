import datetime

from django.db import migrations, models


def migrate_infinite_reservations(apps, schema_editor):
    Machine = apps.get_model("data", "Machine")

    Machine.objects.filter(reserved_until__date=datetime.date.max).update(
        reserved_permanently=True,
        reserved_until=None,
    )


class Migration(migrations.Migration):

    dependencies = [
        ("data", "0057_serialconsoletype_has_ipmi_sol"),
    ]

    operations = [
        migrations.AddField(
            model_name="machine",
            name="reserved_permanently",
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(
            migrate_infinite_reservations,
            migrations.RunPython.noop,
        ),
    ]
