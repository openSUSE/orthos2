import logging
from typing import TYPE_CHECKING, Union

from django.db import models

if TYPE_CHECKING:
    from django.db.models.expressions import Combinable

    from orthos2.data.models.machine import Machine

logger = logging.getLogger("models")


class Component(models.Model):
    class Meta:  # type: ignore
        abstract = True

    machine: "models.ForeignKey[Union[Combinable, Machine], Machine]" = (
        models.ForeignKey("data.Machine", on_delete=models.CASCADE, null=False)
    )
