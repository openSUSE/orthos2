# Generated by Django 4.2.14 on 2024-08-04 10:05
from django.apps.registry import Apps
from django.db import migrations, models
from django.db.backends.base.schema import BaseDatabaseSchemaEditor


def delete_setup_list_commands(apps: Apps, schema_editor: BaseDatabaseSchemaEditor):
    """
    Drop the row "setup.list.command". It is not required anymore due to the switch to the Cobbler XML-RPC API.
    """
    model = apps.get_model("data", "ServerConfig")
    list_command = model.objects.filter(key="setup.list.command")
    if list_command.exists():
        list_command.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("data", "0040_alter_bmc_fence_name_remove_domain_cobbler_server_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="domain",
            name="cobbler_server_password",
            field=models.CharField(
                default="cobbler",
                help_text="The password to login to Cobbler via XML-RPC.",
                max_length=255,
                verbose_name="Cobbler server password",
            ),
        ),
        migrations.AddField(
            model_name="domain",
            name="cobbler_server_username",
            field=models.CharField(
                default="cobbler",
                help_text="The username to login to Cobbler via XML-RPC.",
                max_length=255,
                verbose_name="Cobbler server username",
            ),
        ),
        migrations.AlterField(
            model_name="bmc",
            name="fence_name",
            field=models.CharField(
                choices=[("redfish", "redfish"), ("ipmilanplus", "ipmilanplus")],
                max_length=255,
                verbose_name="Fence agent",
            ),
        ),
        migrations.AlterField(
            model_name="remotepowerdevice",
            name="fence_name",
            field=models.CharField(
                choices=[("apc", "apc")], max_length=255, verbose_name="Fence Agent"
            ),
        ),
        migrations.RunPython(delete_setup_list_commands),
    ]
