# Generated by Django 3.1.4 on 2021-07-13 10:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0025_auto_20210713_0755'),
    ]

    operations = [
        migrations.RenameField(
            model_name='machine',
            old_name='virtualization_api',
            new_name='virt_api_int',
        ),
    ]
