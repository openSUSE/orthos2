from django.db import models
from .machine import Machine
from orthos2.utils.remotepowertype import get_remote_power_type_choices


class BMC(models.Model):
    username = models.CharField(max_length=256, blank=True)
    password = models.CharField(max_length=256, blank=True)
    fqdn = models.CharField(max_length=256)
    mac = models.CharField(max_length=17)
    machine = models.OneToOneField(Machine, on_delete=models.CASCADE)

    remotepower_type_choices = get_remote_power_type_choices("bmc")
    fence_name = models.CharField(choices=remotepower_type_choices,
                                  max_length=255,
                                  verbose_name="Fence agent")

    def __str__(self):
        return self.fqdn
