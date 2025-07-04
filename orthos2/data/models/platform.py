from typing import TYPE_CHECKING, Tuple, Union, cast

from django.contrib import admin
from django.db import models

from .vendor import Vendor

if TYPE_CHECKING:
    from django.db.models.expressions import Combinable

    from orthos2.data.models.enclosure import Enclosure


class PlatformManager(models.Manager["Platform"]):
    def get_by_natural_key(self, name: str) -> "Platform":
        return self.get(name=name)


class Platform(models.Model):
    class Meta:  # type: ignore
        ordering = ["vendor", "name"]

    id: int

    name: "models.CharField[str, str]" = models.CharField(max_length=200, blank=False)

    vendor: "models.ForeignKey[Union[Combinable, Vendor], Vendor]" = models.ForeignKey(
        Vendor, blank=False, null=False, on_delete=models.CASCADE
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

    objects = PlatformManager()

    def natural_key(self) -> Tuple[str]:
        return (self.name,)

    natural_key.dependencies = ["data.vendor"]  # type: ignore

    def __str__(self) -> str:
        return self.name

    @admin.display(description="Vendor")
    def get_vendor(self) -> str:
        return self.vendor.name

    @admin.display(description="Enclosures")
    def get_enclosure_count(self) -> int:
        return self.enclosure_set.count()

    @classmethod
    def get_platform_manager(cls) -> PlatformManager:
        """
        Return the enclosure manager.
        """
        return cast(PlatformManager, cls.objects)
