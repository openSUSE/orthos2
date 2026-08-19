import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("data", "0062_manufacturer_netbox_integration"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="Platform",
            new_name="DeviceType",
        ),
        migrations.RenameField(
            model_name="enclosure",
            old_name="platform",
            new_name="device_type",
        ),
        migrations.RenameField(
            model_name="machine",
            old_name="platform",
            new_name="device_type",
        ),
        migrations.AlterField(
            model_name="enclosure",
            name="device_type",
            field=models.ForeignKey(
                blank=True,
                help_text="The Device Type of the Enclosure",
                limit_choices_to={"is_cartridge": False},
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="data.devicetype",
            ),
        ),
    ]
