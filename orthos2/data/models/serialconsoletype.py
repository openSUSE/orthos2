from typing import Optional, Tuple

from django.db import models


class SerialConsoleType(models.Model):
    class Meta:  # type: ignore
        verbose_name = "Serial Console Type"

    class Type:
        @classmethod
        def to_str(cls, index: int) -> str:
            """Return type as string (serial console type name) by index."""
            for type_tuple in SerialConsoleType.objects.all().values_list("id", "name"):
                if int(index) == type_tuple[0]:
                    return type_tuple[1]
            raise Exception(
                "Serial console type with ID '{}' doesn't exist!".format(index)
            )

        @classmethod
        def to_int(cls, name: str) -> int:
            """Return type as integer if name matches."""
            for type_tuple in SerialConsoleType.objects.all().values_list("id", "name"):
                if name.lower() == type_tuple[1].lower():
                    return type_tuple[0]
            raise Exception("Serial console type '{}' not found!".format(name))

    name: "models.CharField[str, str]" = models.CharField(
        max_length=100,
        null=False,
        blank=False,
        unique=True,
    )

    command: "models.CharField[Optional[str], Optional[str]]" = models.CharField(
        max_length=512,
        null=True,
        blank=True,
    )

    comment: "models.CharField[Optional[str], Optional[str]]" = models.CharField(
        max_length=200,
        null=True,
        blank=True,
    )

    def natural_key(self) -> Tuple[str]:
        return (self.name,)

    def __str__(self) -> str:
        return self.name
