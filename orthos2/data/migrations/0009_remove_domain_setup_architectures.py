# Generated by Django 3.1.4 on 2021-05-22 09:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("data", "0008_auto_20210522_1102"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="domain",
            name="setup_architectures",
        ),
    ]
