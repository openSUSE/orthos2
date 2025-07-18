"""
TODO
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional, Tuple

from django.db import models

if TYPE_CHECKING:
    from django.db.models.fields.related_descriptors import RelatedManager

    from orthos2.data.models.bmc import BMC
    from orthos2.data.models.network.ipaddress import IpAddress
    from orthos2.data.models.network.macaddress import MacAddress
    from orthos2.types import MandatoryMachineForeignKey, OptionalMacAddressForeignKey


class NetworkInterface(models.Model):
    class Meta:  # type: ignore
        verbose_name = "Network Interface"
        ordering = ("-primary",)

    machine: "MandatoryMachineForeignKey" = models.ForeignKey(
        "data.Machine",
        related_name="networkinterfaces",
        editable=False,
        on_delete=models.CASCADE,
    )

    ethernet_type: "models.CharField[str, str]" = models.CharField(
        max_length=100,
        blank=True,
    )

    # Leave here but retrieve via Module --> Module Type ==> Create UI cue that this is not in NetBox
    driver_module: "models.CharField[str, str]" = models.CharField(
        max_length=100,
        blank=True,
    )

    name: "models.CharField[str, str]" = models.CharField(
        max_length=20,
        blank=False,
        default="unknown",
    )

    updated: "models.DateTimeField[datetime, datetime]" = models.DateTimeField(
        "Updated at",
        auto_now=True,
    )

    created: "models.DateTimeField[datetime, datetime]" = models.DateTimeField(
        "Created at",
        auto_now_add=True,
    )

    primary_mac_address: "OptionalMacAddressForeignKey" = models.ForeignKey(
        "data.MacAddress",
        on_delete=models.DO_NOTHING,
        null=True,
    )

    mac_addresses: "RelatedManager[MacAddress]"
    ip_addresses: "RelatedManager[IpAddress]"
    bmc: "Optional[BMC]"

    primary_mac_address: "OptionalMacAddressForeignKey" = models.ForeignKey(
        "data.MacAddress",
        on_delete=models.DO_NOTHING,
        null=True,
    )

    mac_addresses: "RelatedManager[MacAddress]"
    ip_addresses: "RelatedManager[IpAddress]"
    bmc: "Optional[BMC]"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # The two attributes below are only used for network interfaces that are attached to a VM.
        self.model = ""
        self.bridge = ""

    def natural_key(self) -> Tuple[str]:
        return (self.name,)

    def __str__(self) -> str:
        return self.name

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.clean()
        return super(NetworkInterface, self).save(*args, **kwargs)
