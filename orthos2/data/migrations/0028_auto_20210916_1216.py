# Generated by Django 3.1.4 on 2021-09-16 10:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0027_auto_20210916_1201'),
    ]

    operations = [
        migrations.AlterField(
            model_name='serialconsole',
            name='kernel_device',
            field=models.CharField(choices=[(0, 'None'), (1, 'ttyS'), (2, 'tty'), (3, 'ttyUSB'), (4, 'ttyAMA')], default=1, help_text='The kernel device string as passed via kernel command line, e.g. ttyS, ttyAMA, ttyUSB,...', max_length=64, verbose_name='Kernel Device'),
        ),
    ]