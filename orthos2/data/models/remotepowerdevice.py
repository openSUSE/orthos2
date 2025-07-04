from typing import Any, Optional, Tuple

from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from orthos2.data.models.serverconfig import ServerConfig
from orthos2.utils.remotepowertype import get_remote_power_type_choices


class RemotePowerDevice(models.Model):
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
    mac: "models.CharField[str, str]" = models.CharField(max_length=17, unique=True)
    url: "models.URLField[str, str]" = models.URLField(
        blank=True,
        help_text="URL of the Webinterface to configure this Power Device.<br>"
        " Power devices should be in a separate management network only reachable via the cobbler server.<br>"
        " In this case the Webinterface might be port forwarded, also check Documentation<br>",
    )

    remotepower_type_choices = get_remote_power_type_choices("rpower_device")

    fence_name: "models.CharField[str, str]" = models.CharField(
        choices=remotepower_type_choices,
        max_length=255,
        verbose_name="Fence Agent",
    )

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
        return self.fqdn + "[" + self.fence_name + "]"
