from typing import TYPE_CHECKING, Optional

from django.db import models
from django.forms import ValidationError

from orthos2.data.validators import validate_mac_address

if TYPE_CHECKING:
    from orthos2.types import (
        MandatoryMachineOneToOneField,
        MandatoryRemotePowerTypeForeignKey,
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
    fqdn: "models.CharField[str, str]" = models.CharField(max_length=256, unique=True)
    mac: "models.CharField[str, str]" = models.CharField(
        max_length=17,
        unique=True,
        validators=[validate_mac_address],
    )
    machine: "MandatoryMachineOneToOneField" = models.OneToOneField(
        "data.Machine",
        on_delete=models.CASCADE,
    )

    fence_agent: "MandatoryRemotePowerTypeForeignKey" = models.ForeignKey(
        "data.RemotePowerType",
        on_delete=models.CASCADE,
        verbose_name="Fence agent",
        help_text="Fence agent for remote power control",
        limit_choices_to={"device": "bmc"},
    )

    ip_address_v4: "models.GenericIPAddressField[Optional[str], Optional[str]]" = (
        models.GenericIPAddressField(
            protocol="IPv4",
            blank=True,
            unique=True,
            null=True,
            verbose_name="IPv4 address",
            help_text="IPv4 address",
        )
    )

    ip_address_v6: "models.GenericIPAddressField[Optional[str], Optional[str]]" = (
        models.GenericIPAddressField(
            protocol="IPv6",
            blank=True,
            unique=True,
            null=True,
            verbose_name="IPv6 address",
            help_text="IPv6 address",
        )
    )

    def natural_key(self) -> str:
        return self.fqdn

    def __str__(self) -> str:
        return self.fqdn

    def clean_fence_agent(self) -> None:
        """
        Validate the fence_agent field to ensure it is of type "hypervisor".
        This method is called automatically by Django's validation system.
        """
        if not self.fence_agent:
            raise ValidationError("Fence name cannot be empty.")
        if self.fence_agent.device != "bmc":  # type: ignore
            raise ValidationError(
                "The fence agent must be of type 'hypervisor'. "
                "Please select a valid fence agent."
            )
