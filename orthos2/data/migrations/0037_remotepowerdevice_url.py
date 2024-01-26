# Generated by Django 3.2.8 on 2022-02-17 11:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0036_alter_serialconsole_kernel_device'),
    ]

    operations = [
        migrations.AddField(
            model_name='remotepowerdevice',
            name='url',
            field=models.URLField(blank=True, help_text='URL of the Webinterface to configure this Power Device\nPower devices should be in a separate management network only reachable via the cobbler server\nIn this case the Webinterface might be port forwarded, see example below\nSee documentation about more Details.http://cobbler.arch.suse.de:10018'),
        ),
    ]