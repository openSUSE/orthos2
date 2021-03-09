import logging
import os
import re
import socket
import sys
import telnetlib
import time
from urllib import request

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.template import Context, Template
from orthos2.utils.misc import execute, get_s390_hostname
from orthos2.utils.ssh import SSH
from . import ServerConfig

class RemotePower(models.Model):

    class Action:
        ON = 'on'
        OFF = 'off'
        OFF_SSH = 'off-ssh'
        OFF_REMOTEPOWER = 'off-remotepower'
        REBOOT = 'reboot'
        REBOOT_SSH = 'reboot-ssh'
        REBOOT_REMOTEPOWER = 'reboot-remotepower'
        STATUS = 'status'

        as_list = [
            ON,
            OFF,
            REBOOT,
            STATUS,
            OFF_SSH,
            OFF_REMOTEPOWER,
            REBOOT_SSH,
            REBOOT_REMOTEPOWER
        ]

  

    class Status:
        UNKNOWN = 0
        ON = 1
        OFF = 2
        BOOT = 3
        SHUTDOWN = 4
        PAUSED = 5

        @classmethod
        def to_str(cls, index):
            return {
                cls.UNKNOWN: 'unknown',
                cls.ON: 'on',
                cls.OFF: 'off',
                cls.BOOT: 'boot',
                cls.SHUTDOWN: 'shut down',
                cls.PAUSED: 'paused'
            }.get(index, 'undefined')


    kind = models.ForeignKey(
        'data.RemotePowerType',
        verbose_name= 'Powerswitch Type',
        on_delete=models.CASCADE
    )

    machine = models.OneToOneField(
        'data.Machine',
        on_delete=models.CASCADE,
        primary_key=True
    )

   
    management_bmc = models.OneToOneField(
        'data.BMC',
        verbose_name='Management BMC',
        related_name='managed_remotepower',
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )

    remote_power_device = models.ForeignKey(
        'data.RemotePowerDevice',
        related_name='+',
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )

    hypervisor = models.ForeignKey(
        'data.Machine',
        related_name='+',
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    port = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )



    comment = models.CharField(
        max_length=200,
        null=True,
        blank=True
    )

    updated = models.DateTimeField(
        'Updated at',
        auto_now=True
    )

    created = models.DateTimeField(
        'Created at',
        auto_now_add=True
    )


    def save(self, *args, **kwargs):
        """Check values before saving the remote power object. Do only save if type is set."""
        self.clean()

        # check for `None` explicitly because type 0 results in false
        if self.kind is not None:
            super(RemotePower, self).save(*args, **kwargs)
        else:
            raise ValidationError("No remote power type set!")

    def clean(self):
        """
        Check for every remote power type if all required fields are set and deletes unutilized
        values.
        """
        errors = []

        if self.kind.switching_device == "rpower_device":
            if  self.remote_power_device:
                self.management_bmc = None
                self.hypervisor = None
            else:
                errors.append(ValidationError("Please provide a remote power device!"))

        if self.kind.switching_device == "bmc":
            if self.machine.bmc:
                self.management_bmc = self.machine.bmc
                self.hypervisor = None
                self.remote_power_device = None
            else:
                errors.append(ValidationError("The machine needs to have an associated BMC"))
        
        if self.kind.switching_device == "hypervisor":
            if not self.machine.hypervisor:
                errors.append(ValidationError("No hypervisor found!"))
            else:
                self.hypervisor = self.machine.hypervisor
                self.management_bmc = None
                self.remote_power_device = None

        if self.kind.use_port:
            if self.port is None: # test for None, as port may be 0
                errors.append(ValidationError("Please provide a port!"))
        else:
            self.port = None


        if errors:
            raise ValidationError(errors)

    @property
    def name(self):
        if self.kind is None:
            return None
        return str(self.kind.switching_device)

    def power_on(self):
        """Power on the machine."""
        self._perform('on')

    def power_off(self):
        """Power off the machine."""
        self._perform('off')

    def reboot(self):
        """Reboot the machine."""
        self._perform('reboot')

    def get_status(self):
        """Return the current power status."""
        status = self.Status.UNKNOWN
        result = self._perform('status')

        if result and isinstance(result, int):
            status = result
        elif result and result.lower().find('off') > -1:
            status = self.Status.OFF
        elif result and result.lower().find('on') > -1:
            status = self.Status.ON

        return status

    
    def _perform(self, action: str):
        from orthos2.utils.cobbler import CobblerServer
        server =CobblerServer(self.machine.fqdn, self.machine.fqdn)
        result= server.powerswitch(action)
        return result

    def get_credentials(self):
        """
        Return username and password for a login on the switching device
        Use Values from the approrpriate device object, If they don't exist
        fall back to the server config. If that does not exist either, raise an
        exception.
        Returns a Tuple (username, password)
        """
        password = None
        username = None

        if self.kind.switching_device == "bmc":
            username = self.management_bmc.username
            password = self.management_bmc.password
        elif  self.kind.switching_device == "rpower_device":
            username = self.remote_power_device.username
            password = self.remote_power_device.password

        if not username:
            username  = ServerConfig.objects.by_key('remotepower.default.username')
        if not password:
            password = ServerConfig.objects.by_key('remotepower.default.password')

        if not username:
            raise ValueError("Username not available")

        if not password:
            raise ValueError("Password not available")

    def get_power_address(self):
        if self.kind.switching_device == "bmc":
            return self.management_bmc.fqdn
        if self.kind.switching_device == "rpower_device":
            return self.remote_power_device.fqdn
        if self.kind.switching_device == "hypervisor":
            return self.hypervisor.fqdn
        
    def __str__(self):
        return  self.kind.fence + "@" + self.kind.switching_device