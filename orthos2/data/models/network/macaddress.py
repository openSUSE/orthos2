"""
TODO
"""

from django.db import models

from orthos2.data.validators import validate_mac_address


class MacAddress(models.Model):
    """
    TODO
    """

    network_interface = models.ForeignKey(
        "data.NetworkInterface",
        related_name="mac_addresses",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name="Network Interface",
        help_text="Network interface associated with this MAC address",
    )

    mac_address = models.CharField(
        "MAC address",
        max_length=20,
        blank=False,
        unique=True,
        validators=[validate_mac_address],
    )

    primary = models.BooleanField(
        default=False,
        verbose_name="Primary MAC",
        help_text="Indicates if this is the primary MAC address for the machine",
    )

    def __str__(self) -> str:
        return self.mac_address

    def natural_key(self) -> str:
        return self.mac_address
