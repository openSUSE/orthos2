from django.db import models
from orthos2.utils.remotepowertype import get_remote_power_type_choices


class RemotePowerDevice(models.Model):
    username = models.CharField(max_length=256, blank=True, null=True)
    password = models.CharField(max_length=256, blank=True, null=True)
    fqdn = models.CharField(max_length=256, unique=True)
    mac = models.CharField(max_length=17, unique=True)

    remotepower_type_choices = get_remote_power_type_choices("rpower_device")

    fence_name = models.CharField(
                                  choices=remotepower_type_choices,
                                  max_length=255,
                                  verbose_name="Fence Agent"
                                  )

    def natural_key(self):
        return (self.fqdn,)

    def __str__(self):
        return self.fqdn + "[" + self.fence_name + "]"
