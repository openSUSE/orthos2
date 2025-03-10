from typing import TYPE_CHECKING, Any, List, Optional, Tuple

from django.core.exceptions import ValidationError
from django.db import models

from orthos2.utils.misc import is_valid_mac_address

if TYPE_CHECKING:
    from orthos2.data.models.machine import Machine


def validate_mac_address(mac_address: str) -> None:
    """Validate MAC address format."""
    if not is_valid_mac_address(mac_address):
        raise ValidationError("'{}' is not a valid MAC address!".format(mac_address))


def is_unique_mac_address(
    mac_address: str, exclude: Optional[List[str]] = None
) -> bool:
    """
    Check if `mac_address` does already exists.

    Exlcude all MAC addresses in `exclude`.
    """
    if exclude is None:
        exclude = []
    mac_addresses = NetworkInterface.objects.filter(mac_address=mac_address).exclude(
        mac_address__in=exclude
    )

    if mac_addresses.count() > 0:
        return False
    return True


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

        if not is_unique_mac_address(self.mac_address, exclude=exclude):
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
