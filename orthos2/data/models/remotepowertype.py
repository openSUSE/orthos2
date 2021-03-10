from django.db import models
from django.conf import settings
class RemotePowerType(models.Model):
    class Switching_Device(models.TextChoices):
        rpower_device = "rpower_device", "Remotepower Device (e. g. Raritan)"
        bmc = "bmc", "BMC"
        supervisor = "hypervisor", "Hypervisor (physical host)"
    
    switching_device = models.CharField(max_length=64, choices=Switching_Device.choices)
    name = models.CharField(max_length=255)
    use_key = models.BooleanField("Use SSH Key")
    use_port = models.BooleanField("Use Port")
    
    fencing_agents = settings.FENCIG_AGENTS
    if fencing_agents:
        fencing_agents = [(name, name) for name in fencing_agents]
    else:
        fencing_agents = [("None", "None")]
    fence = models.CharField("Fencing Agent", choices=fencing_agents, max_length=255)
    def __str__(self):
        return self.name