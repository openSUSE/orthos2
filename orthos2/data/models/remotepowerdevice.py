from typing import TYPE_CHECKING, Any, Optional, Tuple, cast

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.forms import ValidationError

from orthos2.data.models.serverconfig import ServerConfig
from orthos2.data.validators import validate_mac_address

if TYPE_CHECKING:
    from orthos2.types import MandatoryRemotePowerTypeForeignKey


class RemotePowerDeviceManager(models.Manager["RemotePowerDevice"]):
    """
    Custom manager for RemotePowerDevice to provide additional methods if needed.
    """

    def get_by_natural_key(self, fqdn: str) -> "RemotePowerDevice":
        """
        Get a RemotePowerDevice instance by its natural key (fqdn).
        """
        return self.get(fqdn=fqdn)


class RemotePowerDevice(models.Model):
    # Annotate to allow type checking of autofield
    id: int

    username: "models.CharField[Optional[str], Optional[str]]" = models.CharField(
        max_length=256,
        blank=False,
        null=True,
    )
    password: "models.CharField[Optional[str], Optional[str]]" = models.CharField(
        max_length=256,
        blank=False,
        null=True,
    )
    fqdn: "models.CharField[str, str]" = models.CharField(max_length=256, unique=True)
    mac: "models.CharField[str, str]" = models.CharField(
        max_length=17,
        unique=True,
        validators=[validate_mac_address],
    )
    url: "models.URLField[str, str]" = models.URLField(
        blank=True,
        help_text="URL of the Webinterface to configure this Power Device.<br>"
        " Power devices should be in a separate management network only reachable via the cobbler server.<br>"
        " In this case the Webinterface might be port forwarded, also check Documentation<br>",
    )

    fence_agent: "MandatoryRemotePowerTypeForeignKey" = models.ForeignKey(
        "data.RemotePowerType",
        on_delete=models.CASCADE,
        verbose_name="Fence agent",
        limit_choices_to={"device": "rpowerdevice"},
    )

    objects = RemotePowerDeviceManager()

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        documentation_url: str = ServerConfig.get_server_config_manager().by_key(  # type: ignore
            "orthos.documentation.url",
            "http://localhost",
        )
        power_doc = documentation_url + "/" + "powerswitches.html"
        self._meta.get_field("url").help_text += (  # type: ignore
            '<a href="' + power_doc + '" target="_blank"></a><br>'
        )
        super().__init__(*args, **kwargs)

    @staticmethod
    def get_by_str(fqdn_dev: str) -> Optional["RemotePowerDevice"]:
        if not fqdn_dev:
            return None
        fqdn = fqdn_dev.split("[")[0]
        try:
            return RemotePowerDevice.objects.get(fqdn=fqdn)  # type: ignore
        except ObjectDoesNotExist:
            return None

    def natural_key(self) -> Tuple[str]:
        return (self.fqdn,)

    def __str__(self) -> str:
        return self.fqdn + "[" + self.fence_agent.name + "]"

    @classmethod
    def get_remotepowerdevice_manager(cls) -> RemotePowerDeviceManager:
        """
        Return the RemotePowerDeviceManager instance.
        """
        return cast(RemotePowerDeviceManager, cls.objects)

    def clean_fence_agent(self) -> None:
        """
        Validate the fence_agent field to ensure it is of type "hypervisor".
        This method is called automatically by Django's validation system.
        """
        if not self.fence_agent:
            raise ValidationError("Fence name cannot be empty.")
        if self.fence_agent.device != "rpower_device":  # type: ignore
            raise ValidationError(
                "The fence agent must be of type 'hypervisor'. "
                "Please select a valid fence agent."
            )
