"""
TODO
"""

from typing import TYPE_CHECKING

from django.db import models
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from orthos2.types import (
        MandatoryCharField,
        MandatoryDateField,
        MandatoryNetboxOrthosComparisionRunForeignKey,
        MandatoryUUIDField,
        OptionalBMCForeignKey,
        OptionalEnclosureForeignKey,
        OptionalMachineForeignKey,
        OptionalNetworkInterfaceForeignKey,
    )


class NetboxOrthosComparisionRun(models.Model):
    """
    Represents a run of the NetBox and Orthos comparison task.
    """

    class NetboxOrthosComparisionItemTypes(models.TextChoices):
        """
        Choices for the types of objects that can be compared.
        """

        BMC = "bmc", _("BMC")  # type: ignore
        ENCLOSURE = "enclosure", _("Enclosure")  # type: ignore
        MACHINE = "machine", _("Machine")  # type: ignore
        NETWORK_INTERFACE = "network_interface", _("Network Interface")  # type: ignore

    run_id: "MandatoryUUIDField" = models.UUIDField(primary_key=True, editable=False)
    compare_timestamp: "MandatoryDateField" = models.DateTimeField(blank=False)
    object_type: "MandatoryCharField" = models.CharField(
        choices=NetboxOrthosComparisionItemTypes.choices, max_length=50, blank=False
    )
    object_bmc: "OptionalBMCForeignKey" = models.ForeignKey(
        "data.BMC",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="netboxorthoscomparisionruns",
    )
    object_enclosure: "OptionalEnclosureForeignKey" = models.ForeignKey(
        "data.Enclosure",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="netboxorthoscomparisionruns",
    )
    object_machine: "OptionalMachineForeignKey" = models.ForeignKey(
        "data.Machine",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="netboxorthoscomparisionruns",
    )
    object_network_interface: "OptionalNetworkInterfaceForeignKey" = models.ForeignKey(
        "data.NetworkInterface",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="netboxorthoscomparisionruns",
    )

    def clean(self) -> None:
        super().clean()
        if self.object_type == self.NetboxOrthosComparisionItemTypes.BMC.value:
            if not self.object_bmc:
                raise ValueError("BMC object must be provided for BMC comparison.")
        elif self.object_type == self.NetboxOrthosComparisionItemTypes.ENCLOSURE.value:
            if not self.object_enclosure:
                raise ValueError(
                    "Enclosure object must be provided for Enclosure comparison."
                )
        elif self.object_type == self.NetboxOrthosComparisionItemTypes.MACHINE.value:
            if not self.object_machine:
                raise ValueError(
                    "Machine object must be provided for Machine comparison."
                )
        elif (
            self.object_type
            == self.NetboxOrthosComparisionItemTypes.NETWORK_INTERFACE.value
        ):
            if not self.object_network_interface:
                raise ValueError(
                    "Network Interface object must be provided for Network Interface comparison."
                )


class NetboxOrthosComparisionResult(models.Model):
    """
    Represents a comparison result between NetBox and Orthos for a specific property of an object.
    """

    run_id: "MandatoryNetboxOrthosComparisionRunForeignKey" = models.ForeignKey(
        NetboxOrthosComparisionRun,
        on_delete=models.CASCADE,
        blank=False,
        related_name="results",
    )
    property_name: "MandatoryCharField" = models.CharField(max_length=255, blank=False)
    orthos_result: "MandatoryCharField" = models.CharField(max_length=255, blank=False)
    netbox_result: "MandatoryCharField" = models.CharField(max_length=255, blank=False)
