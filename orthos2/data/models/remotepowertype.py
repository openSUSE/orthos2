"""
Module to define the RemotePowerType model.
"""

from typing import TYPE_CHECKING, Tuple, cast

from django.db import models

if TYPE_CHECKING:
    from orthos2.data.models.architecture import Architecture
    from orthos2.data.models.system import System


class RemotePowerTypeManager(models.Manager["RemotePowerType"]):
    """
    Custom manager for RemotePowerType to provide additional methods if needed.
    """

    def get_by_natural_key(self, name: str) -> "RemotePowerType":
        """
        Get a RemotePowerType instance by its natural key (name).
        """
        return self.get(name=name)


class RemotePowerType(models.Model):
    """
    This model represents a type of remote power control. Currently all power types can be categorized into the three
    cateogories of BMC, Remote Power Devices (e.g. PDUs) and Hypervisor Power Control.
    """

    # Annotate to allow type checking of autofield
    id: int

    name: "models.CharField[str, str]" = models.CharField(
        max_length=255, unique=True, verbose_name="Remote Power Type"
    )

    device: "models.CharField[str, str]" = models.CharField(
        choices=[
            ("bmc", "BMC"),
            ("rpowerdevice", "Remote Power Device"),
            ("hypervisor", "Hypervisor"),
        ],
        blank=True,
        verbose_name="Device",
        max_length=128,
        help_text="Device type for remote power control",
    )
    username: "models.CharField[str, str]" = models.CharField(
        max_length=256,
        blank=True,
        verbose_name="Username",
        help_text="Username for remote power control",
    )

    password: "models.CharField[str, str]" = models.CharField(
        max_length=256,
        blank=True,
        verbose_name="Password",
        help_text="Password for remote power control",
    )

    identity_file: "models.CharField[str, str]" = models.CharField(
        max_length=256,
        blank=True,
        verbose_name="Identity File",
        help_text="Path to identity file for SSH authentication",
    )

    architectures: "models.ManyToManyField[Architecture, Architecture]" = (
        models.ManyToManyField(
            "data.Architecture",
            related_name="remotepowertypes",
            blank=True,
            verbose_name="Supported Architectures",
            help_text="Architectures supported by this remote power type",
        )
    )

    systems: "models.ManyToManyField[System, System]" = models.ManyToManyField(
        "data.System",
        related_name="remotepowertypes",
        blank=True,
        verbose_name="Supported Systems",
        help_text="Systems supported by this remote power type",
    )

    use_port: "models.BooleanField[bool, bool]" = models.BooleanField(
        default=False,
        verbose_name="Use Port",
        help_text="Whether to use a specific port for remote power control",
    )

    use_hostname_as_port: "models.BooleanField[bool, bool]" = models.BooleanField(
        default=False,
        verbose_name="Use Hostname as Port",
        help_text="Whether to use the hostname as the port for remote power control",
    )

    objects = RemotePowerTypeManager()

    def __str__(self) -> str:
        return self.name

    def natural_key(self) -> Tuple[str]:
        return (self.name,)

    @classmethod
    def get_remotepowertype_manager(cls) -> RemotePowerTypeManager:
        """
        Return the architecture manager.
        """
        return cast(RemotePowerTypeManager, cls.objects)
