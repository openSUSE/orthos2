import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("data", "0061_rename_vendor_to_manufacturer"),
    ]

    operations = [
        migrations.AddField(
            model_name="manufacturer",
            name="description",
            field=models.CharField(
                blank=True,
                default="",
                editable=False,
                help_text="Description of the Manufacturer, synchronized from NetBox.",
                max_length=512,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="manufacturer",
            name="netbox_id",
            field=models.PositiveIntegerField(
                default=0,
                help_text="The ID that NetBox gives to the object.",
                verbose_name="NetBox ID",
            ),
        ),
        migrations.AddField(
            model_name="manufacturer",
            name="netbox_last_fetch_attempt",
            field=models.DateTimeField(
                blank=True, null=True, verbose_name="NetBox Last Fetched at"
            ),
        ),
        migrations.AddField(
            model_name="netboxorthoscomparisionrun",
            name="object_manufacturer",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="netboxorthoscomparisionruns",
                to="data.manufacturer",
            ),
        ),
        migrations.AlterField(
            model_name="netboxorthoscomparisionrun",
            name="object_type",
            field=models.CharField(
                choices=[
                    ("bmc", "BMC"),
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
