from typing import TYPE_CHECKING

from django.db import models

from .machine import Machine

if TYPE_CHECKING:
    from orthos2.types import MandatoryDateTimeField, MandatoryMachineForeignKey


class ReservationHistory(models.Model):
    class Meta:  # type: ignore
        ordering = ["-created"]

    machine: "MandatoryMachineForeignKey" = models.ForeignKey(
        Machine,
        editable=False,
        on_delete=models.CASCADE,
    )

    reserved_at: "MandatoryDateTimeField" = models.DateTimeField(
        blank=False,
        null=False,
    )

    reserved_until: "MandatoryDateTimeField" = models.DateTimeField(
        blank=False,
        null=False,
    )

    reserved_reason: "models.CharField[str, str]" = models.CharField(
        "Reservation reason",
        max_length=512,
        blank=False,
        null=False,
    )

    updated: "MandatoryDateTimeField" = models.DateTimeField(
        "Updated at",
        auto_now=True,
    )

    created: "MandatoryDateTimeField" = models.DateTimeField(
        "Created at",
        auto_now_add=True,
    )

    def __str__(self) -> str:
        return "{} ({} - {})".format(
            self.machine.fqdn, self.reserved_at, self.reserved_until
        )
