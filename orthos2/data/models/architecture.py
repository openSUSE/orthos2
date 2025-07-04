from copy import deepcopy
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional, Tuple, cast

from django.contrib import admin
from django.db import models

if TYPE_CHECKING:
    from orthos2.data.models.machine import Machine


class ArchitectureManager(models.Manager["Architecture"]):
    def get_by_natural_key(self, name: str) -> "Architecture":
        return self.get(name=name)


class Architecture(models.Model):

    # Annotate to allow type checking of autofield
    id: int

    name: "models.CharField[str, str]" = models.CharField(
        max_length=200,
        blank=False,
        unique=True,
    )

    dhcp_filename: "models.CharField[Optional[str], Optional[str]]" = models.CharField(
        "DHCP filename",
        max_length=64,
        null=True,
        blank=True,
    )

    contact_email: "models.EmailField[str, str]" = models.EmailField(blank=True)

    updated: "models.DateTimeField[datetime, datetime]" = models.DateTimeField(
        "Updated at",
        auto_now=True,
    )

    created: "models.DateTimeField[datetime, datetime]" = models.DateTimeField(
        "Created at",
        auto_now_add=True,
    )

    default_profile: "models.CharField[Optional[str], Optional[str]]" = (
        models.CharField(
            "Default profile",
            max_length=128,
            null=True,
            blank=True,
        )
    )

    machine_set: models.Manager["Machine"]

    objects = ArchitectureManager()

    def natural_key(self) -> Tuple[str]:
        return (self.name,)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Deep copy object for comparison in `save()`."""
        super(Architecture, self).__init__(*args, **kwargs)

        if self.pk is not None:
            self._original = deepcopy(self)
        else:
            self._original = None

    def __str__(self) -> str:
        return self.name

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Save architecture object."""
        super(Architecture, self).save(*args, **kwargs)

        # check if DHCP needs to be regenerated
        if self._original is not None:
            if self.dhcp_filename != self._original.dhcp_filename:
                from orthos2.data.signals import signal_cobbler_sync_dhcp

                # FIXME: domain_id cannot be None
                signal_cobbler_sync_dhcp.send(sender=self.__class__, domain_id=None)  # type: ignore

    @admin.display(description="Machines")
    def get_machine_count(self) -> int:
        return self.machine_set.count()

    def get_support_contact(self) -> Optional[str]:
        """Return email address for responsible support contact."""
        if self.contact_email:
            return self.contact_email

        return None

    @classmethod
    def get_architecture_manager(cls) -> ArchitectureManager:
        """
        Return the architecture manager.
        """
        return cast(ArchitectureManager, cls.objects)
