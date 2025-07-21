"""
TODO
"""

from typing import TYPE_CHECKING

from django.db import models

if TYPE_CHECKING:
    from orthos2.types import (
        MandatoryCharField,
        ManyToManyNetworkInterfaceField,
        OptionalGenericIPAddressField,
    )


class IpAddress(models.Model):
    """
    TODO
    """

    network_interface: "ManyToManyNetworkInterfaceField" = models.ManyToManyField(
        "data.NetworkInterface",
        related_name="ip_addresses",
        blank=True,
        verbose_name="Network Interface",
        help_text="Network interface associated with this IP address",
    )

    ip_address: "OptionalGenericIPAddressField" = models.GenericIPAddressField(
        protocol="both",
        unique=True,
        blank=False,
        verbose_name="IP address",
        help_text="IP address",
    )

    protocol: "MandatoryCharField" = models.CharField(
        max_length=10,
        choices=[("IPv4", "IPv4"), ("IPv6", "IPv6")],
        default="IPv4",
        verbose_name="Protocol",
        help_text="IP protocol type (IPv4 or IPv6)",
        blank=False,
    )

    dns_name: "MandatoryCharField" = models.CharField(
        max_length=256,
        blank=True,
        verbose_name="DNS Name",
        help_text="DNS Name associated with the IP address",
    )

    def __str__(self) -> str:
        return self.ip_address or "No IP Address"

    def natural_key(self) -> str:
        return self.ip_address or "No IP Address"
