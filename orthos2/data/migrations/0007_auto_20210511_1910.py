# Generated by Django 3.1.4 on 2021-05-11 17:10

import django.db.models.deletion
from django.db import migrations, models

import orthos2.data.models.domain
import orthos2.data.models.machine


class Migration(migrations.Migration):

    dependencies = [
        ("data", "0006_auto_20210511_0917"),
    ]

    operations = [
        migrations.AlterField(
            model_name="machine",
            name="administrative",
            field=models.BooleanField(
                default=False,
                help_text="Administrative machines cannot be reserved",
                verbose_name="Administrative machine",
            ),
        ),
        migrations.AlterField(
            model_name="machine",
            name="bios_date",
            field=models.DateTimeField(
                default="1990-10-03T10:00:00+00:00",
                editable=False,
                help_text="The firmware BIOS is from ... (on x86 as retrieved from dmidecode -s bios-version",
            ),
        ),
        migrations.AlterField(
            model_name="machine",
            name="bios_version",
            field=models.CharField(
                blank=True,
                help_text="The firmware BIOS is from ... (on x86 as retrieved from dmidecode -s bios-version",
                max_length=200,
            ),
        ),
        migrations.AlterField(
            model_name="machine",
            name="comment",
            field=models.CharField(
                blank=True,
                help_text="Machine specific problems or extras you want to tell others?",
                max_length=512,
            ),
        ),
        migrations.AlterField(
            model_name="machine",
            name="cpu_cores",
            field=models.IntegerField(
                default=1, help_text="Amount of CPU cores", verbose_name="CPU cores"
            ),
        ),
        migrations.AlterField(
            model_name="machine",
            name="cpu_flags",
            field=models.TextField(
                blank=True,
                help_text="CPU feature/bug flags as exported from the kernel (/proc/cpuinfo)",
                verbose_name="CPU flags",
            ),
        ),
        migrations.AlterField(
            model_name="machine",
            name="cpu_id",
            field=models.CharField(
                blank=True,
                help_text="X86 cpuid value which identifies the CPU family/model/stepping and features",
                max_length=200,
                verbose_name="CPU ID",
            ),
        ),
        migrations.AlterField(
            model_name="machine",
            name="cpu_model",
            field=models.CharField(
                blank=True,
                help_text="The domain name of the primary NIC",
                max_length=200,
                verbose_name="CPU model",
            ),
        ),
        migrations.AlterField(
            model_name="machine",
            name="cpu_threads",
            field=models.IntegerField(
                default=1, help_text="Amount of CPU threads", verbose_name="CPU threads"
            ),
        ),
        migrations.AlterField(
            model_name="machine",
            name="efi",
            field=models.BooleanField(
                default=False,
                help_text="Installed in EFI (aarch64/x86) mode?",
                verbose_name="EFI boot",
            ),
        ),
        migrations.AlterField(
            model_name="machine",
            name="enclosure",
            field=models.ForeignKey(
                blank=True,
                help_text="Enclosure/chassis of one or more machines",
                on_delete=django.db.models.deletion.CASCADE,
                to="data.enclosure",
            ),
        ),
        migrations.AlterField(
            model_name="machine",
            name="fqdn",
            field=models.CharField(
                db_index=True,
                help_text="The Fully Qualified Domain Name of the main network interface of the machine",
                max_length=200,
                unique=True,
                validators=[
                    orthos2.data.models.machine.validate_dns,
                    orthos2.data.models.domain.validate_domain_ending,
                ],
                verbose_name="FQDN",
            ),
        ),
        migrations.AlterField(
            model_name="machine",
            name="fqdn_domain",
            field=models.ForeignKey(
                help_text="The domain name of the primary NIC",
                on_delete=django.db.models.deletion.CASCADE,
                to="data.domain",
            ),
        ),
        migrations.AlterField(
            model_name="machine",
            name="ipmi",
            field=models.BooleanField(
                default=False,
                help_text="IPMI service processor (BMC) detected",
                verbose_name="IPMI capability",
            ),
        ),
        migrations.AlterField(
            model_name="machine",
            name="nda",
            field=models.BooleanField(
                default=False,
                help_text="This machine is under NDA and has secret (early development HW?) partner information, do not share any data to the outside world",
                verbose_name="NDA hardware",
            ),
        ),
        migrations.AlterField(
            model_name="machine",
            name="product_code",
            field=models.CharField(
                blank=True,
                help_text="The product code can be read from a sticker on the machine's chassis (e.g. S1DL1SEXA)",
                max_length=200,
            ),
        ),
        migrations.AlterField(
            model_name="machine",
            name="reserved_reason",
            field=models.CharField(
                blank=True,
                help_text="Why do you need this machine (bug no, jira feature, what do you test/work on)?",
                max_length=512,
                null=True,
                verbose_name="Reservation reason",
            ),
        ),
        migrations.AlterField(
            model_name="machine",
            name="reserved_until",
            field=models.DateTimeField(
                blank=True,
                help_text="Reservation expires at xx.yy.zzzz (max 90 days)",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="machine",
            name="serial_number",
            field=models.CharField(
                blank=True,
                help_text="The serial number can be read from a sticker on the machine's chassis (e.g. GPDRDP5022003)",
                max_length=200,
            ),
        ),
        migrations.AlterField(
            model_name="machine",
            name="status_ipv4",
            field=models.SmallIntegerField(
                choices=[
                    (0, "unreachable"),
                    (1, "reachable"),
                    (2, "confirmed"),
                    (3, "MAC mismatch"),
                    (4, "address mismatch"),
                    (5, "no address assigned"),
                    (6, "address-family disabled"),
                ],
                default=0,
                editable=False,
                help_text="Does this IPv4 address respond to ping?",
                verbose_name="Status IPv4",
            ),
        ),
        migrations.AlterField(
            model_name="machine",
            name="status_ipv6",
            field=models.SmallIntegerField(
                choices=[
                    (0, "unreachable"),
                    (1, "reachable"),
                    (2, "confirmed"),
                    (3, "MAC mismatch"),
                    (4, "address mismatch"),
                    (5, "no address assigned"),
                    (6, "address-family disabled"),
                ],
                default=0,
                editable=False,
                help_text="Does this IPv6 address respond to ping?",
                verbose_name="Status IPv6",
            ),
        ),
        migrations.AlterField(
            model_name="machine",
            name="status_login",
            field=models.BooleanField(
                default=False,
                editable=False,
                help_text="Can orthos log into this host via ssh key (if not scanned data might be outdated)?",
                verbose_name="Login",
            ),
        ),
        migrations.AlterField(
            model_name="machine",
            name="status_ssh",
            field=models.BooleanField(
                default=False,
                editable=False,
                help_text="Is the ssh port (22) on this host address open?",
                verbose_name="SSH",
            ),
        ),
        migrations.AlterField(
            model_name="machine",
            name="use_bmc",
            field=models.BooleanField(
                default=True,
                help_text="Create and connect a networkinterace as BMC in a new form further down after saving",
                verbose_name="Use BMC",
            ),
        ),
        migrations.AlterField(
            model_name="machine",
            name="virtualization_api",
            field=models.SmallIntegerField(
                blank=True,
                choices=[(0, "libvirt")],
                help_text="Only supported API currently is libvirt",
                null=True,
                verbose_name="Virtualization API",
            ),
        ),
        migrations.AlterField(
            model_name="machine",
            name="vm_auto_delete",
            field=models.BooleanField(
                default=False,
                help_text="Release and destroy virtual machine instances, once people have released (do not reserve anymore) them",
                verbose_name="Delete automatically",
            ),
        ),
        migrations.AlterField(
            model_name="machine",
            name="vm_capable",
            field=models.BooleanField(
                default=False,
                help_text="Do the CPUs support native virtualization (KVM). This field is deprecated",
                verbose_name="VM capable",
            ),
        ),
        migrations.AlterField(
            model_name="machine",
            name="vm_dedicated_host",
            field=models.BooleanField(
                default=False,
                help_text="Dedicated to serve as physical host for virtual machines (users cannot reserve this machine)",
                verbose_name="Dedicated VM host",
            ),
        ),
        migrations.AlterField(
            model_name="machine",
            name="vm_max",
            field=models.IntegerField(
                default=5,
                help_text="Maximum amount of virtual hosts allowed to be spawned on this virtual server (ToDo: don't use yet)",
                verbose_name="Max. VMs",
            ),
        ),
    ]
