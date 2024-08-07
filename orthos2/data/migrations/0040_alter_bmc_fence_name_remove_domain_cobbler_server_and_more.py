# Generated by Django 4.2.3 on 2023-07-27 11:17

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("data", "0039_auto_20220221_1649"),
    ]

    operations = [
        migrations.AlterField(
            model_name="bmc",
            name="fence_name",
            field=models.CharField(
                choices=[], max_length=255, verbose_name="Fence agent"
            ),
        ),
        migrations.RemoveField(
            model_name="domain",
            name="cobbler_server",
        ),
        migrations.AlterField(
            model_name="machine",
            name="check_connectivity",
            field=models.SmallIntegerField(
                choices=[
                    (0, "Disable"),
                    (1, "Ping only"),
                    (2, "SSH (includes Ping+SSH)"),
                    (3, "Full (includes Ping+SSH+Login)"),
                ],
                default=3,
                help_text="Nightly checks whether the machine responds to ping, ssh port is open or whether orthos canlog in via ssh key. Can be triggered manually via command line client: `rescan [fqdn] status`",
            ),
        ),
        migrations.AlterField(
            model_name="machine",
            name="platform",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="data.platform",
            ),
        ),
        migrations.AlterField(
            model_name="machine",
            name="vm_auto_delete",
            field=models.BooleanField(
                default=False,
                help_text="Release and destroy virtual machine instances, once people have released(do not reserve anymore) them",
                verbose_name="Delete automatically",
            ),
        ),
        migrations.AlterField(
            model_name="remotepower",
            name="fence_name",
            field=models.CharField(
                choices=[], max_length=255, verbose_name="Fence Agent"
            ),
        ),
        migrations.AlterField(
            model_name="remotepowerdevice",
            name="fence_name",
            field=models.CharField(
                choices=[], max_length=255, verbose_name="Fence Agent"
            ),
        ),
        migrations.AlterField(
            model_name="remotepowerdevice",
            name="url",
            field=models.URLField(
                blank=True,
                help_text="URL of the Webinterface to configure this Power Device.<br> Power devices should be in a separate management network only reachable via the cobbler server.<br> In this case the Webinterface might be port forwarded, also check Documentation<br>",
            ),
        ),
        migrations.AddField(
            model_name="domain",
            name="cobbler_server",
            field=models.ForeignKey(
                blank=True,
                limit_choices_to={"administrative": True},
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="cobbler_server_for",
                to="data.machine",
                verbose_name="Cobbler server",
            ),
        ),
    ]
