# Generated by Django 3.1.4 on 2021-05-05 14:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("data", "0003_auto_20210406_1905"),
    ]

    operations = [
        migrations.AddField(
            model_name="remotepower",
            name="options",
            field=models.CharField(
                blank=True,
                default="",
                help_text='Additional command line options to be passed to the fence agent.\n        E. g. "--management=<management LPAR> for lpar',
                max_length=1024,
            ),
        ),
        migrations.AlterField(
            model_name="bmc",
            name="password",
            field=models.CharField(blank=True, default="", max_length=256),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="bmc",
            name="username",
            field=models.CharField(blank=True, default="", max_length=256),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="remotepower",
            name="fence_name",
            field=models.CharField(
                choices=[
                    ("virsh", "virsh"),
                    ("lpar", "lpar"),
                    ("ibmz", "ibmz"),
                    ("redfish", "redfish"),
                ],
                max_length=255,
                verbose_name="Fence Agent",
            ),
        ),
        migrations.AlterField(
            model_name="remotepowerdevice",
            name="fence_name",
            field=models.CharField(
                choices=[("raritan", "raritan"), ("apc", "apc")],
                max_length=255,
                verbose_name="Fence Agent",
            ),
        ),
    ]
