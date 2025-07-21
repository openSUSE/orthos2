from datetime import datetime
from typing import TYPE_CHECKING, Any, Iterable, Optional, Tuple

from django.core.exceptions import ValidationError
from django.db import models

from orthos2.data.validators import validate_mac_address
from orthos2.utils import misc

if TYPE_CHECKING:
    from orthos2.types import MandatoryMachineForeignKey


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

    primary: "models.BooleanField[bool, bool]" = models.BooleanField(
        "Primary",
        blank=False,
        default=False,
    )

    mac_address: "models.CharField[str, str]" = models.CharField(
        "MAC address",
        max_length=20,
        blank=False,
        unique=True,
        validators=[validate_mac_address],
    )

    ip_address_v4: "models.GenericIPAddressField[Optional[str], Optional[str]]" = (
        models.GenericIPAddressField(
            protocol="IPv4",
            unique=True,
            null=True,
            blank=True,
            verbose_name="IPv4 address",
            help_text="IPv4 address",
        )
    )

    ip_address_v6: "models.GenericIPAddressField[Optional[str], Optional[str]]" = (
        models.GenericIPAddressField(
            protocol="IPv6",
            unique=True,
            null=True,
            blank=True,
            verbose_name="IPv6 address",
            help_text="IPv6 address",
        )
    )

    ethernet_type: "models.CharField[str, str]" = models.CharField(
        max_length=100,
        blank=True,
    )

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

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # The two attributes below are only used for network interfaces that are attached to a VM.
        self.model = ""
        self.bridge = ""

    def natural_key(self) -> Tuple[str]:
        return (self.mac_address,)

    def __str__(self) -> str:
        if self.primary:
            return "{} ({}/{})".format(self.mac_address, self.name, "primary")
        return "{} ({})".format(self.mac_address, self.name)

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.clean()
        return super(NetworkInterface, self).save(*args, **kwargs)

    def clean(self) -> None:
        """Validate, convert to upper case and check if MAC address already exists."""
        self.mac_address = self.mac_address.upper()
        validate_mac_address(self.mac_address)

        exclude: Iterable[str] = []
        if hasattr(self, "machine"):
            exclude = self.machine.networkinterfaces.all().values_list(
                "mac_address", flat=True
            )

        if not misc.is_unique_mac_address(self.mac_address, exclude=exclude):
            violate_net = NetworkInterface.objects.get(mac_address=self.mac_address)
            if hasattr(violate_net, "machine"):
                violate_machine = violate_net.machine.fqdn
            else:
                violate_machine = "networkinterface not assigned to a machine"
            raise ValidationError(
                "MAC address '{}' is already in use by: {}".format(
                    self.mac_address, violate_machine
                )
            )
