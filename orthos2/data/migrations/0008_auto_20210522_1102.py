# Generated by Django 3.1.4 on 2021-05-22 09:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0007_auto_20210511_1910'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bmc',
            name='fence_name',
            field=models.CharField(choices=[('redfish', 'redfish'), ('ipmilanplus', 'ipmilanplus')], max_length=255, verbose_name='Fence agent'),
        ),
        migrations.AlterField(
            model_name='remotepower',
            name='fence_name',
            field=models.CharField(choices=[('virsh', 'virsh'), ('pvm', 'pvm'), ('lpar', 'lpar'), ('ibmz', 'ibmz')], max_length=255, verbose_name='Fence Agent'),
        ),
    ]