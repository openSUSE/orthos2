import datetime

from django.db import migrations, models
from django.utils import timezone


def migrate_infinite_reservations(apps, schema_editor):
    Machine = apps.get_model("data", "Machine")
    import pytz

    utc = pytz.utc
    infinite = timezone.datetime.combine(datetime.date.max, datetime.time.min)
    infinite = timezone.make_aware(infinite, utc)
    Machine.objects.filter(reserved_until=infinite).update(
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
