from datetime import datetime
from typing import Tuple, cast

from django.db import models


class SystemManager(models.Manager["System"]):
    def get_by_natural_key(self, name: str) -> "System":
        return self.get(name=name)


class System(models.Model):

    help_text = "Describes the system type of a machine"

    # Annotate to allow type checking of autofield
    id: int

    name: "models.CharField[str, str]" = models.CharField(
        max_length=200,
        blank=False,
        unique=True,
        help_text="What kind of system are these machines?",
    )

    virtual: "models.BooleanField[bool, bool]" = models.BooleanField(
        default=False,
        null=False,
        blank=False,
        help_text="Are these machines virtual systems (can have a hypervisor)?",
    )

    allowBMC: "models.BooleanField[bool, bool]" = models.BooleanField(
        default=False,
        null=False,
        blank=False,
        help_text="Can a network interface be assigned to such a system serving as BMC?",
    )

    allowHypervisor: "models.BooleanField[bool, bool]" = models.BooleanField(
        default=False,
        null=False,
        blank=False,
        help_text="Can such systems host virtual machines?",
    )

    administrative: "models.BooleanField[bool, bool]" = models.BooleanField(
        default=False,
        null=False,
        blank=False,
        help_text="Are these machines administrative systems (cannot be installed or reserved)?",
    )

    created: "models.DateTimeField[datetime, datetime]" = models.DateTimeField(
        "created at",
        auto_now=True,
    )

    objects = SystemManager()

    def natural_key(self) -> Tuple[str]:
        return (self.name,)

    def __str__(self) -> str:
        return self.name

    @classmethod
    def get_system_manager(cls) -> SystemManager:
        """
        Return the system manager.
        """
        return cast(SystemManager, cls.objects)
