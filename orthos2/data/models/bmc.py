from django.db import models

from orthos2.data.models.machine import Machine
from orthos2.data.validators import validate_mac_address
from orthos2.utils.remotepowertype import get_remote_power_type_choices


class BMC(models.Model):
    username = models.CharField(max_length=256, blank=True)
    password = models.CharField(max_length=256, blank=True)
    fqdn = models.CharField(max_length=256, unique=True)
    mac = models.CharField(
        max_length=17, unique=True, validators=[validate_mac_address]
    )
    machine = models.OneToOneField(Machine, on_delete=models.CASCADE)

    remotepower_type_choices = get_remote_power_type_choices("bmc")
    fence_name = models.CharField(
        choices=remotepower_type_choices, max_length=255, verbose_name="Fence agent"
    )

    ip_address_v4 = models.GenericIPAddressField(
        protocol="IPv4",
        blank=True,
        unique=True,
        null=True,
        verbose_name="IPv4 address",
        help_text="IPv4 address",
    )

    ip_address_v6 = models.GenericIPAddressField(
        protocol="IPv6",
        blank=True,
        unique=True,
        null=True,
        verbose_name="IPv6 address",
        help_text="IPv6 address",
    )

    def natural_key(self) -> str:
        return self.fqdn

    def __str__(self) -> str:
        return self.fqdn
