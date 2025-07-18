"""
TODO
"""

from typing import TYPE_CHECKING

from django.db import models
from django.forms import ValidationError

if TYPE_CHECKING:
    from orthos2.types import (
        MandatoryRemotePowerTypeForeignKey,
        ManyToManyMachineField,
        OptionalNetworkInterfaceForeignKey,
    )


class BMC(models.Model):
    username: "models.CharField[str, str]" = models.CharField(
        max_length=256,
        blank=True,
    )
    password: "models.CharField[str, str]" = models.CharField(
        max_length=256,
        blank=True,
    )
    machine: "ManyToManyMachineField" = models.ManyToManyField("data.Machine")

    fence_agent: "MandatoryRemotePowerTypeForeignKey" = models.ForeignKey(
        "data.RemotePowerType",
        on_delete=models.CASCADE,
    )

    fence_agent: "MandatoryRemotePowerTypeForeignKey" = models.ForeignKey(
        "data.RemotePowerType",
        on_delete=models.CASCADE,
        verbose_name="Fence agent",
        help_text="Fence agent for remote power control",
        limit_choices_to={"device": "bmc"},
    )

    network_interface: "OptionalNetworkInterfaceForeignKey" = models.ForeignKey(
        "data.NetworkInterface",
        related_name="bmc",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name="Network Interface",
        help_text="Network interface used for BMC connection",
    )

    """
    # TODO: Do we need a natural key for this model?
    def natural_key(self) -> str:
        return self.fqdn

    # FIXME: Find good string representation
    def __str__(self) -> str:
        return ""
    """

    def clean_fence_agent(self) -> None:
        """
        Validate the fence_agent field to ensure it is of type "bmc".
        This method is called automatically by Django's validation system.
        """
        if not self.fence_agent:
            raise ValidationError("Fence name cannot be empty.")
        if self.fence_agent.device != "bmc":  # type: ignore
            raise ValidationError(
                "The fence agent must be of type 'bmc'. Please select a valid fence agent."
            )
