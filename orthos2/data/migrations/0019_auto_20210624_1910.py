# Generated by Django 3.1.4 on 2021-06-24 17:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("data", "0017_auto_20210622_1848"),
    ]

    operations = [
        migrations.AlterField(
            model_name="remotepowerdevice",
            name="fqdn",
            field=models.CharField(max_length=256, unique=True),
        ),
        migrations.AlterField(
            model_name="remotepowerdevice",
            name="mac",
            field=models.CharField(max_length=17, unique=True),
        ),
    ]
