from typing import Optional, Tuple

from django.db import models


class Vendor(models.Model):
    class Manager(models.Manager["Vendor"]):
        def get_by_natural_key(self, name: str) -> Optional["Vendor"]:
            return self.get(name=name)

    class Meta:
        ordering = ["name"]

    name = models.CharField(max_length=100, blank=False, unique=True)

    objects = Manager()

    def natural_key(self) -> Tuple[str]:
        return (self.name,)

    def __str__(self) -> str:
        return self.name
