"""
TODO
"""

from typing import TYPE_CHECKING

from django.db import models

from orthos2.data.validators import validate_mac_address

if TYPE_CHECKING:
    from orthos2.types import (
        MandatoryBooleanField,
        MandatoryCharField,
        OptionalNetworkInterfaceForeignKey,
    )


class MacAddress(models.Model):
    """
    TODO
    """

    network_interface: "OptionalNetworkInterfaceForeignKey" = models.ForeignKey(
        "data.NetworkInterface",
        related_name="mac_addresses",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name="Network Interface",
        help_text="Network interface associated with this MAC address",
    )

    # TODO: Make upercase and check uniqeness
    mac_address: "MandatoryCharField" = models.CharField(
        "MAC address",
        max_length=20,
        blank=False,
        unique=True,
        validators=[validate_mac_address],
    )

    primary: "MandatoryBooleanField" = models.BooleanField(
        default=False,
        verbose_name="Primary MAC",
        help_text="Indicates if this is the primary MAC address for the machine",
    )

    def __str__(self) -> str:
        return self.mac_address

    def natural_key(self) -> str:
        return self.mac_address
