# Generated by Django 3.2.8 on 2022-02-21 15:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("data", "0038_auto_20220221_1626"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="machine",
            name="installed_distro",
        ),
        migrations.AlterField(
            model_name="machine",
            name="active",
            field=models.BooleanField(
                default=True,
                help_text="Machine vanishes from most lists. This is intendend as kind of maintenance/repair state",
            ),
        ),
        migrations.AlterField(
            model_name="machine",
            name="autoreinstall",
            field=models.BooleanField(
                default=True,
                help_text="Shall this machine be automatically re-installed when its reservation ends?<br>The last installation that has been triggered will be used for auto re-installation.",
                verbose_name="Auto re-install machine",
            ),
        ),
    ]
