from django.db import models
from .machine import Machine
class RemotePowerDevice(models.Model):
    username = models.CharField(max_length=256, blank=True, null=True)
    password = models.CharField(max_length=256, blank=True, null=True)
    fqdn = models.CharField(max_length=256)
    mac = models.CharField(max_length=17)
    
    def __str__(self):
        return self.fqdn
