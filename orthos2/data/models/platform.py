from typing import TYPE_CHECKING, Tuple

from django.contrib import admin
from django.db import models

from .vendor import Vendor

if TYPE_CHECKING:
    from orthos2.data.models.enclosure import Enclosure


class Platform(models.Model):
    class Meta:
        ordering = ["vendor", "name"]

    id: int

    name = models.CharField(max_length=200, blank=False)

    vendor = models.ForeignKey(
        Vendor, blank=False, null=False, on_delete=models.CASCADE
    )

    is_cartridge = models.BooleanField("Cartridge/Blade", default=False)

    description = models.CharField(max_length=512, blank=True)

    enclosure_set: models.Manager["Enclosure"]

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
