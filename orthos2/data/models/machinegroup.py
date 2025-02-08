from copy import deepcopy
from typing import Any, Optional, Tuple

from django.contrib.auth.models import User
from django.db import models


class MachineGroup(models.Model):
    class Meta:
        ordering = ["-name"]
        verbose_name = "Machine Group"

    name = models.CharField(max_length=100, blank=False, unique=True)

    members = models.ManyToManyField(User, through="MachineGroupMembership")  # type: ignore

    comment = models.CharField(max_length=512, blank=True)

    contact_email = models.EmailField(blank=True)

    dhcp_filename = models.CharField(
        "DHCP filename", max_length=64, null=True, blank=True
    )

    tftp_server = models.ForeignKey(
        "data.Machine",
        related_name="tftp_server_for_group",
        verbose_name="TFTP server",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        limit_choices_to={"administrative": True},
    )

    setup_use_architecture = models.BooleanField(
        "Use machines architecture for setup", default=False
    )

    def natural_key(self) -> Tuple[str]:
        return (self.name,)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Deep copy object for comparison in `save()`."""
        super(MachineGroup, self).__init__(*args, **kwargs)

        if self.pk is not None:
            self._original = deepcopy(self)
        else:
            self._original = None

    def __str__(self) -> str:
        return self.name

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Save machine group object."""
        super(MachineGroup, self).save(*args, **kwargs)

        # check if DHCP needs to be regenerated
        if self._original is not None:
            if self.dhcp_filename != self._original.dhcp_filename:
                from orthos2.data.signals import signal_cobbler_sync_dhcp

                # FIXME: domain_id cannot be None
                signal_cobbler_sync_dhcp.send(sender=self.__class__, domain_id=None)

    def clean(self) -> None:
        """
        Camel case machine group name.

        Eliminate spaces for further string processing like setup during first creation;
        remove whitespaces during edit.
        """
        if self.pk is None:
            self.name = "".join(
                char for char in self.name.title() if not char.isspace()
            )
        else:
            self.name = self.name.replace(" ", "")

    def get_support_contact(self) -> Optional[str]:
        """Return email address for responsible support contact."""
        if self.contact_email:
            return self.contact_email

        return None


class MachineGroupMembership(models.Model):
    user = models.ForeignKey(User, related_name="memberships", on_delete=models.CASCADE)

    group = models.ForeignKey(MachineGroup, on_delete=models.CASCADE)

    is_privileged = models.BooleanField(default=False, null=False)

    def __str__(self) -> str:
        return "{} | {}".format(self.user, self.group)
