from django.db import models
from .machine import Machine
class BMC(models.Model):
    username = models.CharField(max_length=256)
    password = models.CharField(max_length=256)
    fqdn = models.CharField(max_length=256)
    mac = models.CharField(max_length=17)
    machine = models.OneToOneField(Machine, on_delete=models.CASCADE)
    def __str__(self):
        return self.fqdn
