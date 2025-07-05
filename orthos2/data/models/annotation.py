import datetime
from typing import TYPE_CHECKING, Tuple

from django.contrib.auth.models import User
from django.db import models

if TYPE_CHECKING:
    from orthos2.types import (
        MandatoryDateTimeField,
        MandatoryMachineForeignKey,
        OptionalUserForeignKey,
    )


class Annotation(models.Model):
    class Meta:  # type: ignore
        ordering = ["-created"]

    # Annotate to allow type checking of autofield
    id: int

    machine: "MandatoryMachineForeignKey" = models.ForeignKey(
        "data.Machine",
        related_name="annotations",
        editable=False,
        blank=False,
        on_delete=models.CASCADE,
    )

    text: "models.CharField[str, str]" = models.CharField(max_length=1024, blank=False)

    reporter: "OptionalUserForeignKey" = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=False, editable=False
    )

    created: "MandatoryDateTimeField" = models.DateTimeField(
        "Created at",
        auto_now_add=True,
    )

    def natural_key(self) -> Tuple[str, datetime.date]:
        return self.machine.fqdn, self.created

    def __str__(self) -> str:
        return self.machine.fqdn
