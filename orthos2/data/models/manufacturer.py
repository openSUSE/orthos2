from typing import Tuple, cast

from django.db import models


class ManufacturerManager(models.Manager["Manufacturer"]):
    def get_by_natural_key(self, name: str) -> "Manufacturer":
        return self.get(name=name)


class Manufacturer(models.Model):
    class Meta:  # type: ignore
        ordering = ["name"]

    name: "models.CharField[str, str]" = models.CharField(
        max_length=100,
        blank=False,
        unique=True,
    )

    objects = ManufacturerManager()

    def natural_key(self) -> Tuple[str]:
        return (self.name,)

    def __str__(self) -> str:
        return self.name

    @classmethod
    def get_manufacturer_manager(cls) -> ManufacturerManager:
        """
        Return the manufacturer manager.
        """
        return cast(ManufacturerManager, cls.objects)
