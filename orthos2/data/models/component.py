import logging
from typing import TYPE_CHECKING

from django.db import models

if TYPE_CHECKING:
    from orthos2.data.models.machine import Machine

logger = logging.getLogger("models")


class Component(models.Model):
    class Meta:
        abstract = True

    machine = models.ForeignKey["Machine"](  # type: ignore
        "data.Machine", on_delete=models.CASCADE, null=False
    )
