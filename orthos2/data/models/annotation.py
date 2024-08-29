import datetime
from typing import TYPE_CHECKING, Tuple

from django.contrib.auth.models import User
from django.db import models

if TYPE_CHECKING:
    from orthos2.data.models.machine import Machine


class Annotation(models.Model):
    class Meta:
        ordering = ["-created"]

    machine = models.ForeignKey["Machine"](  # type: ignore
        "data.Machine",
        related_name="annotations",
        editable=False,
        blank=False,
        on_delete=models.CASCADE,
    )

    text = models.CharField(max_length=1024, blank=False)

    reporter = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=False, editable=False
    )

    created = models.DateTimeField("Created at", auto_now_add=True)

    def natural_key(self) -> Tuple[str, datetime.date]:
        return self.machine.fqdn, self.created  # type: ignore

    def __str__(self) -> str:
        return self.machine.fqdn  # type: ignore
