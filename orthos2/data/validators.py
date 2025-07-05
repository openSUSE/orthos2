import validators  # type: ignore
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_mac_address(mac_address: str) -> None:
    """Validate MAC address format."""
    if not validators.mac_address(mac_address):  # type: ignore
        raise ValidationError("'{}' is not a valid MAC address!".format(mac_address))
