# Generated by Django 3.1.4 on 2021-06-22 16:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("data", "0016_auto_20210616_1122"),
    ]

    operations = [
        migrations.AddField(
            model_name="machine",
            name="unknown_mac",
            field=models.BooleanField(
                default=False,
                help_text="Use this to create a BMC before the mac address of the machine is known",
                verbose_name="MAC unknwon",
            ),
        ),
        migrations.AlterField(
            model_name="machine",
            name="vm_max",
            field=models.IntegerField(
                default=6,
                help_text="Maximum amount of virtual hosts allowed to be spawned on this virtual server (ToDo: don't use yet)",
                verbose_name="Max. VMs",
            ),
        ),
    ]
