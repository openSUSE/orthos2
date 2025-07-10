from typing import TYPE_CHECKING

from django.db import models

from .machine import Machine

if TYPE_CHECKING:
    from orthos2.types import MandatoryMachineForeignKey


class Installation(models.Model):
    machine: "MandatoryMachineForeignKey" = models.ForeignKey(
        Machine,
        related_name="installations",
        editable=False,
        on_delete=models.CASCADE,
    )

    active: "models.BooleanField[bool, bool]" = models.BooleanField(
        blank=False,
        default=True,
    )

    architecture: "models.CharField[str, str]" = models.CharField(
        max_length=200,
        blank=True,
    )

    distribution: "models.CharField[str, str]" = models.CharField(
        max_length=200,
        blank=True,
    )

    kernelversion: "models.CharField[str, str]" = models.CharField(
        "Kernel version",
        max_length=100,
        blank=True,
    )

    partition: "models.CharField[str, str]" = models.CharField(
        max_length=100,
        blank=True,
    )

    def __str__(self) -> str:
        if self.active:
            return "{} ({})".format(self.distribution, "active")
        return self.distribution
