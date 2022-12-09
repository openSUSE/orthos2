from django.db import models
from django.core.exceptions import ObjectDoesNotExist

from orthos2.utils.remotepowertype import get_remote_power_type_choices
from . import ServerConfig


class RemotePowerDevice(models.Model):
    username = models.CharField(max_length=256, blank=False, null=True)
    password = models.CharField(max_length=256, blank=False, null=True)
    fqdn = models.CharField(max_length=256, unique=True)
    mac = models.CharField(max_length=17, unique=True)
    url = models.URLField(
        blank=True,
        help_text="URL of the Webinterface to configure this Power Device.<br>" +
        "Power devices should be in a separate management network only reachable via the cobbler server.<br>" +
        "In this case the Webinterface might be port forwarded, also check Documentation<br>"
    )


    remotepower_type_choices = get_remote_power_type_choices("rpower_device")

    fence_name = models.CharField(
                                  choices=remotepower_type_choices,
                                  max_length=255,
                                  verbose_name="Fence Agent"
                                  )

    def __init__(self, *args, **kwargs):
        power_doc = ServerConfig.objects.by_key('orthos.documentation.url', "http://localhost") \
                    + "/" + "powerswitches.html"
        self.url.help_text += "<a href=\"" + power_doc + "\" target=\"_blank\"></a><br>"
        super(models.Model, self).__init__(*args, **kwargs)
    @staticmethod
    def get_by_str(fqdn_dev):
        if not fqdn_dev:
            return
        fqdn = fqdn_dev.split('[')[0]
        try:
            return RemotePowerDevice.objects.get(fqdn=fqdn)
        except ObjectDoesNotExist:
            return None

    def natural_key(self):
        return (self.fqdn,)

    def __str__(self):
        return self.fqdn + "[" + self.fence_name + "]"
