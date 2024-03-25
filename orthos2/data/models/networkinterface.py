from typing import TYPE_CHECKING, Any, Tuple

from django.core.exceptions import ValidationError
from django.db import models

from orthos2.data.validators import validate_mac_address
from orthos2.utils import misc

if TYPE_CHECKING:
    from orthos2.data.models.machine import Machine


class NetworkInterface(models.Model):
    class Meta:
        verbose_name = "Network Interface"
        ordering = ("-primary",)

    machine = models.ForeignKey["Machine"](  # type: ignore
        "data.Machine",
        related_name="networkinterfaces",
        editable=False,
        on_delete=models.CASCADE,
    )

    primary = models.BooleanField("Primary", blank=False, default=False)

    mac_address = models.CharField(
        "MAC address",
        max_length=20,
        blank=False,
        unique=True,
        validators=[validate_mac_address],
    )

    ip_address_v4 = models.GenericIPAddressField(
        protocol="IPv4",
        unique=True,
        null=True,
        blank=True,
        verbose_name="IPv4 address",
        help_text="IPv4 address",
    )

    ip_address_v6 = models.GenericIPAddressField(
        protocol="IPv6",
        unique=True,
        null=True,
        blank=True,
        verbose_name="IPv6 address",
        help_text="IPv6 address",
    )

    ethernet_type = models.CharField(
        max_length=100,
        blank=True,
    )

    driver_module = models.CharField(
        max_length=100,
        blank=True,
    )

    name = models.CharField(max_length=20, blank=False, default="unknown")

    updated = models.DateTimeField("Updated at", auto_now=True)

    created = models.DateTimeField("Created at", auto_now_add=True)

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

        if hasattr(self, "machine"):
            exclude = self.machine.networkinterfaces.all().values_list(  # type: ignore
                "mac_address", flat=True
            )
        else:
            exclude = []

        if not misc.is_unique_mac_address(self.mac_address, exclude=exclude):
            violate_net = NetworkInterface.objects.get(mac_address=self.mac_address)
            if hasattr(violate_net, "machine"):
                violate_machine = violate_net.machine.fqdn  # type: ignore
            else:
                violate_machine = "networkinterface not assigned to a machine"
            raise ValidationError(
                "MAC address '{}' is already in use by: {}".format(
                    self.mac_address, violate_machine
                )
            )
