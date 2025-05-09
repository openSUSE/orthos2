# Generated by Django 4.2.20 on 2025-04-04 10:14

import socket
from typing import List, NamedTuple, Optional

import django.core.validators
from django.apps.registry import Apps
from django.db import migrations, models
from django.db.backends.base.schema import BaseDatabaseSchemaEditor

import orthos2.data.models.domain
import orthos2.data.validators


class DNSLookupTuple(NamedTuple):
    """from django.apps.registry import Apps
    Use `ip_version` to specify which IP version gets returned.

    IP versions (`ip_version`):
        4  - ['192.168.0.1', ...]
        6  - ['0:0:0:0:0:ffff:c0a8:1', ...]
        10 - (['192.168.0.1', ...], [0:0:0:0:0:ffff:c0a8:1, ...])
    """

    ipv4: List[str] = []
    ipv6: List[str] = []


def get_ip(fqdn: str, ip_version: int = 4) -> Optional[DNSLookupTuple]:
    """
    Return all IP addresses for FQDN.
    Use `ip_version` to specify which IP version gets returned.
    IP versions (`ip_version`):
        4  - ['192.168.0.1', ...]
        6  - ['0:0:0:0:0:ffff:c0a8:1', ...]
        10 - (['192.168.0.1', ...], [0:0:0:0:0:ffff:c0a8:1, ...])
    """
    ipv4: List[str] = []
    ipv6: List[str] = []

    try:
        result = socket.getaddrinfo(fqdn, None, 0, socket.SOCK_STREAM, socket.SOL_TCP)

        for address_family in result:
            if address_family[0] == socket.AF_INET:
                ipv4.append(address_family[4][0])  # type: ignore
            elif address_family[0] == socket.AF_INET6:
                ipv6.append(address_family[4][0])  # type: ignore
    except (IndexError, socket.gaierror):
        return None

    if not ipv4:
        return None

    if ip_version == 4:
        return DNSLookupTuple(ipv4, [])
    elif ip_version == 6:
        return DNSLookupTuple([], ipv6)
    elif ip_version == 10:
        return DNSLookupTuple(ipv4, ipv6)
    else:
        raise ValueError("Unknown IP version '{}'!".format(ip_version))


def get_ipv4(fqdn: str) -> Optional[str]:
    """Return (first) IPv4 address for FQDN."""
    lookup_result = get_ip(fqdn, ip_version=4)
    if lookup_result and lookup_result.ipv4:
        return lookup_result.ipv4[0]
    return None


def get_ipv6(fqdn: str) -> Optional[str]:
    """Return (first) IPv6 address for FQDN."""
    lookup_result = get_ip(fqdn, ip_version=6)
    if lookup_result and lookup_result.ipv6:
        return lookup_result.ipv6[0]
    return None


def set_ipv4_network_interface_defaults(
    apps: Apps, schema_editor: BaseDatabaseSchemaEditor
):
    NetworkInterface = apps.get_model("data", "NetworkInterface")
    for interface in NetworkInterface.objects.all().iterator():
        if not interface.primary:
            print("Skipping non-primary interface")
            continue
        ipv4_address = get_ipv4(interface.machine.fqdn)
        print(
            f"Interface: {interface.mac_address} FQDN: {interface.machine.fqdn} IPv4: {ipv4_address}"
        )
        interface.ip_address_v4 = ipv4_address
        interface.save()


def set_ipv6_network_interface_defaults(
    apps: Apps, schema_editor: BaseDatabaseSchemaEditor
):
    NetworkInterface = apps.get_model("data", "NetworkInterface")
    for interface in NetworkInterface.objects.all().iterator():
        if not interface.primary:
            print("Skipping non-primary interface")
            continue
        ipv6_address = get_ipv6(interface.machine.fqdn)
        print(
            f"Interface: {interface.mac_address} FQDN: {interface.machine.fqdn} IPv6: {ipv6_address}"
        )
        interface.ip_address_v6 = ipv6_address
        interface.save()


def set_ipv4_bmc_defaults(apps: Apps, schema_editor: BaseDatabaseSchemaEditor):
    BMC = apps.get_model("data", "BMC")
    for bmc in BMC.objects.all().iterator():
        bmc.ip_address_v4 = get_ipv4(bmc.fqdn)
        bmc.save()


def set_ipv6_bmc_defaults(apps: Apps, schema_editor: BaseDatabaseSchemaEditor):
    BMC = apps.get_model("data", "BMC")
    for bmc in BMC.objects.all().iterator():
        bmc.ip_address_v6 = get_ipv6(bmc.fqdn)
        bmc.save()


class Migration(migrations.Migration):

    dependencies = [
        ("data", "0042_alter_machine_last_check"),
    ]

    operations = [
        migrations.AddField(
            model_name="NetworkInterface",
            name="ip_address_v4",
            field=models.GenericIPAddressField(
                blank=True,
                null=True,
                protocol="IPv4",
                unique=True,
                help_text="IPv4 address",
                verbose_name="IPv4 address",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="NetworkInterface",
            name="ip_address_v6",
            field=models.GenericIPAddressField(
                blank=True,
                null=True,
                protocol="IPv6",
                unique=True,
                help_text="IPv6 address",
                verbose_name="IPv6 address",
            ),
            preserve_default=False,
        ),
        migrations.RunPython(
            code=set_ipv4_network_interface_defaults,
        ),
        migrations.RunPython(
            code=set_ipv6_network_interface_defaults,
        ),
        migrations.AddField(
            model_name="bmc",
            name="ip_address_v4",
            field=models.GenericIPAddressField(
                blank=True,
                null=True,
                protocol="IPv4",
                unique=True,
                help_text="IPv4 address",
                verbose_name="IPv4 address",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="bmc",
            name="ip_address_v6",
            field=models.GenericIPAddressField(
                blank=True,
                null=True,
                protocol="IPv6",
                unique=True,
                help_text="IPv6 address",
                verbose_name="IPv6 address",
            ),
            preserve_default=False,
        ),
        migrations.RunPython(
            code=set_ipv4_bmc_defaults,
        ),
        migrations.RunPython(
            code=set_ipv6_bmc_defaults,
        ),
        migrations.AlterField(
            model_name="machine",
            name="fqdn",
            field=models.CharField(
                db_index=True,
                help_text="The Fully Qualified Domain Name of the main network interface of the machine",
                max_length=200,
                unique=True,
                validators=[orthos2.data.models.domain.validate_domain_ending],
                verbose_name="FQDN",
            ),
        ),
        migrations.AddField(
            model_name="domain",
            name="dynamic_range_v4_end",
            field=models.GenericIPAddressField(
                default="127.0.0.1", help_text="The end of the range.", protocol="IPv4"
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="domain",
            name="dynamic_range_v4_start",
            field=models.GenericIPAddressField(
                default="127.0.0.1",
                help_text="The start of the range.",
                protocol="IPv4",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="domain",
            name="dynamic_range_v6_end",
            field=models.GenericIPAddressField(
                default="::1", help_text="The end of the range.", protocol="IPv6"
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="domain",
            name="dynamic_range_v6_start",
            field=models.GenericIPAddressField(
                default="::1", help_text="The start of the range.", protocol="IPv6"
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="domain",
            name="enable_v4",
            field=models.BooleanField(
                default=True,
                help_text="If IPv4 addresses should be enabled for the network.",
                verbose_name="Enable IPv4 addresses",
            ),
        ),
        migrations.AddField(
            model_name="domain",
            name="enable_v6",
            field=models.BooleanField(
                default=True,
                help_text="If IPv6 addresses should be enabled for the network.",
                verbose_name="Enable IPv6 addresses",
            ),
        ),
        migrations.AddField(
            model_name="domain",
            name="ip_v4",
            field=models.GenericIPAddressField(
                default="127.0.0.1",
                help_text="The IPv4 address of the network.",
                protocol="IPv4",
                verbose_name="IPv4 address",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="domain",
            name="ip_v6",
            field=models.GenericIPAddressField(
                default="::1",
                help_text="The IPv6 address of the network.",
                protocol="IPv6",
                verbose_name="IPv6 address",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="domain",
            name="subnet_mask_v4",
            field=models.PositiveIntegerField(
                default=24,
                help_text="The IPv4 subnet mask of the network.",
                validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(31),
                ],
                verbose_name="IPv4 subnet mask",
            ),
        ),
        migrations.AddField(
            model_name="domain",
            name="subnet_mask_v6",
            field=models.PositiveIntegerField(
                default=64,
                help_text="The IPv6 subnet mask of the network.",
                validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(127),
                ],
                verbose_name="IPv6 subnet mask",
            ),
        ),
        migrations.AlterField(
            model_name="machine",
            name="unknown_mac",
            field=models.BooleanField(
                default=False,
                help_text="Use this to create a BMC before the mac address of the machine is known",
                verbose_name="MAC unknown",
            ),
        ),
        migrations.RemoveField(
            model_name="machine",
            name="unknown_mac",
        ),
        migrations.AlterField(
            model_name="bmc",
            name="mac",
            field=models.CharField(
                max_length=17,
                unique=True,
                validators=[orthos2.data.validators.validate_mac_address],
            ),
        ),
    ]
