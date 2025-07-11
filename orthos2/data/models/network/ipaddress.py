"""
TODO
"""

from django.db import models


class IpAddress(models.Model):
    """
    TODO
    """

    network_interface = models.ManyToManyField(
        "data.NetworkInterface",
        related_name="ip_addresses",
        blank=True,
        verbose_name="Network Interface",
        help_text="Network interface associated with this IP address",
    )

    ip_address = models.GenericIPAddressField(
        protocol="both",
        unique=True,
        null=True,
        blank=True,
        verbose_name="IPv4 address",
        help_text="IPv4 address",
    )

    protocol = models.CharField(
        max_length=10,
        choices=[("IPv4", "IPv4"), ("IPv6", "IPv6")],
        default="both",
        verbose_name="Protocol",
        help_text="IP protocol type (IPv4, IPv6, or both)",
    )

    dns_name = models.CharField(
        max_length=256,
        blank=True,
        verbose_name="DNS Name",
        help_text="DNS Name associated with the IP address",
    )

    def __str__(self) -> str:
        return self.ip_address or "No IP Address"

    def natural_key(self) -> str:
        return self.ip_address or "No IP Address"
