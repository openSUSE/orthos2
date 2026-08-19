from typing import TYPE_CHECKING, Tuple, Union, cast

from django.contrib import admin
from django.db import models

from .manufacturer import Manufacturer

if TYPE_CHECKING:
    from django.db.models.expressions import Combinable

    from orthos2.data.models.enclosure import Enclosure


class DeviceTypeManager(models.Manager["DeviceType"]):
    def get_by_natural_key(self, name: str) -> "DeviceType":
        return self.get(name=name)


class DeviceType(models.Model):
    class Meta:  # type: ignore
        ordering = ["manufacturer", "name"]

    id: int

    name: "models.CharField[str, str]" = models.CharField(max_length=200, blank=False)

    manufacturer: "models.ForeignKey[Union[Combinable, Manufacturer], Manufacturer]" = (
        models.ForeignKey(
            Manufacturer, blank=False, null=False, on_delete=models.CASCADE
        )
    )

    is_cartridge: "models.BooleanField[bool, bool]" = models.BooleanField(
        "Cartridge/Blade",
        default=False,
    )

    description: "models.CharField[str, str]" = models.CharField(
        max_length=512,
        blank=True,
    )

    enclosure_set: models.Manager["Enclosure"]

    objects = DeviceTypeManager()

    def natural_key(self) -> Tuple[str]:
        return (self.name,)

    natural_key.dependencies = ["data.manufacturer"]  # type: ignore

    def __str__(self) -> str:
        return self.name

    @admin.display(description="Manufacturer")
    def get_manufacturer(self) -> str:
        return self.manufacturer.name

    @admin.display(description="Enclosures")
    def get_enclosure_count(self) -> int:
        return self.enclosure_set.count()

    @classmethod
    def get_device_type_manager(cls) -> DeviceTypeManager:
        """
        Return the enclosure manager.
        """
        return cast(DeviceTypeManager, cls.objects)
