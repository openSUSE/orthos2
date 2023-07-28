# Generated by Django 3.1.4 on 2021-06-10 10:46

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0013_auto_20210610_0804'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='architecture',
            name='dhcpv4_write',
        ),
        migrations.RemoveField(
            model_name='architecture',
            name='dhcpv6_write',
        ),
        migrations.RemoveField(
            model_name='machine',
            name='dhcpv4_write',
        ),
        migrations.RemoveField(
            model_name='machine',
            name='dhcpv6_write',
        ),
        migrations.RemoveField(
            model_name='machine',
            name='use_bmc',
        ),
        migrations.RemoveField(
            model_name='machinegroup',
            name='dhcpv4_write',
        ),
        migrations.RemoveField(
            model_name='machinegroup',
            name='dhcpv6_write',
        ),
        migrations.AlterField(
            model_name='machine',
            name='check_connectivity',
            field=models.SmallIntegerField(choices=[(0, 'Disable'), (1, 'Ping only'), (2, 'SSH (includes Ping+SSH)'), (3, 'Full (includes Ping+SSH+Login)')], default=1, help_text='Nightly checks whether the machine responds to ping, ssh port is open or whether orthos can log in via ssh key. Can be triggered manually via command line client: `rescan [fqdn] status`'),
        ),
        migrations.AlterField(
            model_name='machine',
            name='collect_system_information',
            field=models.BooleanField(default=False, help_text='Shall the system be scanned every night? This only works if the proper ssh key is in place in authorized_keys and can be triggered manually via command line client: `rescan [fqdn]`'),
        ),
        migrations.AlterField(
            model_name='machine',
            name='contact_email',
            field=models.EmailField(blank=True, help_text='Override contact email address to whom is in charge for this machine', max_length=254),
        ),
        migrations.AlterField(
            model_name='machine',
            name='dhcp_filename',
            field=models.CharField(blank=True, help_text='Override bootloader binary retrieved from a tftp server (corresponds to the `filename` ISC dhcpd.conf variable)', max_length=64, null=True, verbose_name='DHCP filename'),
        ),
        migrations.AlterField(
            model_name='machine',
            name='hypervisor',
            field=models.ForeignKey(blank=True, help_text='The physical host this virtual machine is running on', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='hypervising', to='data.machine'),
        ),
        migrations.AlterField(
            model_name='machine',
            name='kernel_options',
            field=models.CharField(blank=True, help_text='Additional kernel command line parameters to pass', max_length=4096),
        ),
        migrations.AlterField(
            model_name='machine',
            name='tftp_server',
            field=models.ForeignKey(blank=True, help_text='Override tftp server used for network boot (corresponds to the `next_server` ISC dhcpd.conf variable)', limit_choices_to={'administrative': True}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tftp_server_for', to='data.machine', verbose_name='TFTP server'),
        ),
        migrations.AlterField(
            model_name='serialconsole',
            name='command',
            field=models.CharField(blank=True, help_text='Final command which is constructed using above info and synced to cscreen server /etc/cscreenrc config', max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='serialconsole',
            name='console_server',
            field=models.CharField(blank=True, help_text='DNS resolvable hostname (FQDN) to serial console server', max_length=1024, null=True, verbose_name='Dedicated console server'),
        ),
        migrations.AlterField(
            model_name='serialconsole',
            name='kernel_device',
            field=models.CharField(blank=True, default='ttyS', help_text='The kernel device string as passed via kernel command line, e.g. ttyS, ttyAMA, ttyUSB,...', max_length=255, verbose_name='Kernel Device'),
        ),
        migrations.AlterField(
            model_name='serialconsole',
            name='kernel_device_num',
            field=models.SmallIntegerField(default=0, help_text='The kernel device number is concatenated to the kernel device string (see above).\nA value of 1 might end up in console=ttyS1 kernel command line paramter.', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(1024)], verbose_name='Kernel Device number'),
        ),
        migrations.AlterField(
            model_name='serialconsole',
            name='port',
            field=models.SmallIntegerField(blank=True, help_text='On which physical port of the Dedicated Console Server is this machine connected?', null=True),
        ),
        migrations.AlterField(
            model_name='serialconsole',
            name='stype',
            field=models.ForeignKey(help_text='Mechanism how to set up and retrieve serial console data', on_delete=django.db.models.deletion.CASCADE, to='data.serialconsoletype', verbose_name='Serial Console Type'),
        ),
    ]
