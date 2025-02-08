from typing import Optional, Tuple

from django.db import models

from orthos2.utils.misc import safe_get_or_default


class System(models.Model):
    class Manager(models.Manager["System"]):
        def get_by_natural_key(self, name: str) -> Optional["System"]:
            return self.get(name=name)

    class Type:
        @classmethod
        def prep(cls) -> None:
            """Preparation of const variables for fast and developer-friendly handling."""
            cls.BAREMETAL = safe_get_or_default(System, "name", "BareMetal", "pk", -1)  # type: ignore

    help_text = "Describes the system type of a machine"

    name = models.CharField(
        max_length=200,
        blank=False,
        unique=True,
        help_text="What kind of system are these machines?",
    )

    virtual = models.BooleanField(
        default=False,
        null=False,
        blank=False,
        help_text="Are these machines virtual systems (can have a hypervisor)?",
    )

    allowBMC = models.BooleanField(
        default=False,
        null=False,
        blank=False,
        help_text="Can a network interface be assigned to such a system serving as BMC?",
    )

    allowHypervisor = models.BooleanField(
        default=False,
        null=False,
        blank=False,
        help_text="Can such systems host virtual machines?",
    )

    administrative = models.BooleanField(
        default=False,
        null=False,
        blank=False,
        help_text="Are these machines administrative systems (cannot be installed or reserved)?",
    )

    created = models.DateTimeField("created at", auto_now=True)

    objects = Manager()

    def natural_key(self) -> Tuple[str]:
        return (self.name,)

    def __str__(self) -> str:
        return self.name
