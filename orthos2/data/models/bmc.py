from django.db import models
from . import NetworkInterface
class BMC(models.Model):
    username = models.CharField(max_length=256, name="BMC User", blank=True)
    password = models.CharField(max_length=256, name="BMC Password", blank=True)
    network_interface = models.OneToOneField(NetworkInterface, on_delete=models.CASCADE)
    fqdn = models.CharField(max_length=256, name="FQDN", blank=False)
    mac = models.CharField(max_length=256, name="MAC", blank=False)
    machine = models.ForeignKey('data.Machine', on_delete=models.CASCADE)

def save(self, *args, **kwargs):
    self.network_interface = NetworkInterface.objects.get_or_create(mac_address)
     super(BMC, self).save(*args, **kwargs)

