from django.db import models


class NetboxOrthosComparisionRun(models.Model):
    """
    Represents a run of the NetBox and Orthos comparison task.
    """

    class NetboxOrthosComparisionItemTypes(models.TextChoices):
        """
        Choices for the types of objects that can be compared.
        """

        BMC = "bmc", "BMC"
        ENCLOSURE = "enclosure", "Enclosure"
        MACHINE = "machine", "Machine"
        NETWORK_INTERFACE = "network_interface", "Network Interface"

    run_id = models.UUIDField(primary_key=True, editable=False)
    compare_timestamp = models.DateTimeField(blank=False)
    object_type = models.CharField(
        choices=NetboxOrthosComparisionItemTypes.choices, max_length=50, blank=False
    )
    object_bmc = models.ForeignKey(
        "BMC",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="netboxorthoscomparisionruns",
    )
    object_enclosure = models.ForeignKey(
        "Enclosure",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="netboxorthoscomparisionruns",
    )
    object_machine = models.ForeignKey(
        "Machine",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="netboxorthoscomparisionruns",
    )
    object_network_interface = models.ForeignKey(
        "NetworkInterface",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="netboxorthoscomparisionruns",
    )

    def clean(self) -> None:
        super().clean()
        if self.object_type == self.NetboxOrthosComparisionItemTypes.BMC:
            if not self.object_bmc:
                raise ValueError("BMC object must be provided for BMC comparison.")
        elif self.object_type == self.NetboxOrthosComparisionItemTypes.ENCLOSURE:
            if not self.object_enclosure:
                raise ValueError(
                    "Enclosure object must be provided for Enclosure comparison."
                )
        elif self.object_type == self.NetboxOrthosComparisionItemTypes.MACHINE:
            if not self.object_machine:
                raise ValueError(
                    "Machine object must be provided for Machine comparison."
                )
        elif (
            self.object_type == self.NetboxOrthosComparisionItemTypes.NETWORK_INTERFACE
        ):
            if not self.object_network_interface:
                raise ValueError(
                    "Network Interface object must be provided for Network Interface comparison."
                )


class NetboxOrthosComparisionResult(models.Model):
    """
    Represents a comparison result between NetBox and Orthos for a specific property of an object.
    """

    run_id = models.ForeignKey(
        NetboxOrthosComparisionRun,
        on_delete=models.CASCADE,
        blank=False,
        related_name="results",
    )
    property_name = models.CharField(max_length=255, blank=False)
    orthos_result = models.CharField(max_length=255, blank=False)
    netbox_result = models.CharField(max_length=255, blank=False)
