# Generated by Django 3.1.4 on 2021-07-13 03:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0022_auto_20210628_1713'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='serverconfig',
            name='created',
        ),
        migrations.AlterField(
            model_name='machine',
            name='check_connectivity',
            field=models.SmallIntegerField(choices=[(0, 'Disable'), (1, 'Ping only'), (2, 'SSH (includes Ping+SSH)'), (3, 'Full (includes Ping+SSH+Login)')], default=3, help_text='Nightly checks whether the machine responds to ping, ssh port is open or whether orthos can log in via ssh key. Can be triggered manually via command line client: `rescan [fqdn] status`'),
        ),
        migrations.AlterField(
            model_name='machine',
            name='collect_system_information',
            field=models.BooleanField(default=True, help_text='Shall the system be scanned every night? This only works if the proper ssh key is in place in authorized_keys and can be triggered manually via command line client: `rescan [fqdn]`'),
        ),
        migrations.AlterField(
            model_name='remotepower',
            name='options',
            field=models.CharField(blank=True, default='', help_text='Additional command line options to be passed to the fence agent.\n        E. g. "managed=<management LPAR> for lpar', max_length=1024),
        ),
        migrations.AlterField(
            model_name='serialconsole',
            name='kernel_device',
            field=models.CharField(choices=[('ttyS', 'ttyS'), ('ttyUSB', 'ttyUSB'), ('ttyAMA', 'ttyAMA'), ('tty', 'tty')], default='ttyS', help_text='The kernel device string as passed via kernel command line, e.g. ttyS, ttyAMA, ttyUSB,...', max_length=64, verbose_name='Kernel Device'),
        ),
    ]