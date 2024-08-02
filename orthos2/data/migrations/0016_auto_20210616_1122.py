# Generated by Django 3.1.4 on 2021-06-16 09:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("data", "0015_auto_20210615_1500"),
    ]

    operations = [
        migrations.AlterField(
            model_name="machine",
            name="bios_date",
            field=models.DateField(
                blank=True,
                default=None,
                editable=False,
                help_text="The firmware BIOS is from ... (on x86 as retrieved from dmidecode -s bios-version",
                null=True,
            ),
        ),
    ]
