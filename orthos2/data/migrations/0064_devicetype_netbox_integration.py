import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("data", "0063_rename_platform_to_devicetype"),
    ]

    operations = [
        migrations.AddField(
            model_name="devicetype",
            name="netbox_id",
            field=models.PositiveIntegerField(
                default=0,
                help_text="The ID that NetBox gives to the object.",
                verbose_name="NetBox ID",
            ),
        ),
        migrations.AddField(
            model_name="devicetype",
            name="netbox_last_fetch_attempt",
            field=models.DateTimeField(
                blank=True, null=True, verbose_name="NetBox Last Fetched at"
            ),
        ),
        migrations.AddField(
            model_name="netboxorthoscomparisionrun",
            name="object_device_type",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="netboxorthoscomparisionruns",
                to="data.devicetype",
            ),
        ),
        migrations.AlterField(
            model_name="netboxorthoscomparisionrun",
            name="object_type",
            field=models.CharField(
                choices=[
                    ("bmc", "BMC"),
                    ("device_type", "Device Type"),
                    ("enclosure", "Enclosure"),
                    ("machine", "Machine"),
                    ("manufacturer", "Manufacturer"),
                    ("network_interface", "Network Interface"),
                    ("remote_power_device", "Remote Power Device"),
                ],
                max_length=50,
            ),
        ),
    ]
