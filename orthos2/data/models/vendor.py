from typing import Tuple, cast

from django.db import models


class VendorManager(models.Manager["Vendor"]):
    def get_by_natural_key(self, name: str) -> "Vendor":
        return self.get(name=name)


class Vendor(models.Model):
    class Meta:  # type: ignore
        ordering = ["name"]

    name: "models.CharField[str, str]" = models.CharField(
        max_length=100,
        blank=False,
        unique=True,
    )

    objects = VendorManager()

    def natural_key(self) -> Tuple[str]:
        return (self.name,)

    def __str__(self) -> str:
        return self.name

    @classmethod
    def get_vendor_manager(cls) -> VendorManager:
        """
        Return the vendor manager.
        """
        return cast(VendorManager, cls.objects)
