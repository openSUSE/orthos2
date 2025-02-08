# Generated by Django 3.2.8 on 2021-10-18 14:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("data", "0031_auto_20211006_1005"),
    ]

    operations = [
        migrations.AlterField(
            model_name="domain",
            name="cobbler_server",
            field=models.ManyToManyField(  # type: ignore
                blank=True,
                limit_choices_to={"administrative": True},
                null=True,
                related_name="cobbler_server_for",
                to="data.Machine",
                verbose_name="Cobbler server",
            ),
        ),
    ]
