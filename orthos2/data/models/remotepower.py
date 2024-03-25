import logging

from django.core.exceptions import ValidationError
from django.db import models

from orthos2.utils.remotepowertype import RemotePowerType, get_remote_power_type_choices

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

    remotepower_type_choices = get_remote_power_type_choices("hypervisor")

    fence_name = models.CharField(
        choices=remotepower_type_choices,
        max_length=255,
        verbose_name="Fence Agent"
    )

    machine = models.OneToOneField(
        'data.Machine',
        on_delete=models.CASCADE,
        primary_key=True
    )

    remote_power_device = models.ForeignKey(
        'data.RemotePowerDevice',
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

    options = models.CharField(
        max_length=1024,
        blank=True,
        default="",
        help_text="""Additional command line options to be passed to the fence agent.
        E. g. "managed=<management LPAR> for lpar"""

    )

    def save(self, *args, **kwargs):
        """Check values before saving the remote power object. Do only save if type is set."""

        errors = []
        self.fence_name = self._get_remotepower_fence_name()
        logging.debug("getting fence object for %s", self.fence_name)
        fence = RemotePowerType.from_fence(self.fence_name)
        if fence.device == "rpower_device":
            if fence.use_port:
                if self.port is None:  # test for None, as port may be 0
                    errors.append(ValidationError("Please provide a port!"))
            elif fence.use_hostname_as_port:
                self.port = self.machine.hostname
            else:
                self.port = None
            if self.remote_power_device:
                self.fence_name = self.remote_power_device.fence_name
            else:
                errors.append(ValidationError("Please provide a remote power device!"))
        elif fence.device == "bmc":
            if self.machine.bmc:
                self.fence_name = self.machine.bmc.fence_name
                self.remote_power_device = None
            else:
                errors.append(ValidationError("The machine needs to have an associated BMC"))

        elif fence.device == "hypervisor":
            if self.machine.hypervisor:
                self.remote_power_device = None
            else:
                errors.append(ValidationError("No hypervisor found!"))

        else:
            errors.append(ValidationError(
                "{} is not a valid switching device".format(fence['switching_device'])))

        if errors:
            raise ValidationError(errors)

        # check for `None` explicitly because type 0 results in false
        if self.fence_name is not None:
            super(RemotePower, self).save(*args, **kwargs)
        else:
            raise ValidationError("No remote power type set!")

    def _get_remotepower_fence_name(self):
        if self.fence_name:
            return self.fence_name
        if self.remote_power_device:
            return self.remote_power_device.fence_name
        if self.machine.bmc:
            return self.machine.bmc.fence_name

    @property
    def name(self):
        if self.fence_name is None:
            return None
        logging.debug("getting fence object for %s", self.fence_name)
        return str(RemotePowerType.from_fence(self.fence_name).device)

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
        if not result:
            raise RuntimeError("recieved no result from _perform('status')")
        result = "\n".join(result)

        if result.lower().find('off') > -1:
            status = self.Status.OFF
        elif result.lower().find('on') > -1:
            status = self.Status.ON
        else:
            raise RuntimeError("Inconclusive result from _perform('status')")
        return status

    def _perform(self, action: str) -> str:
        """
        Perform a power action on machine associated to the object

        :param action: The action to perform. Mustbe 'on', 'off', 'reboot' or 'status'
        :returns: A string as retrieved from the underlying power switch tool
        """
        from orthos2.utils.cobbler import CobblerServer
        result = "No Cobbler server found"
        server = CobblerServer.from_machine(self.machine)
        if server:
            result = server.powerswitch(self.machine, action)
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
        fence = RemotePowerType.from_fence(self.fence_name)
        if fence.device == "bmc":
            username = self.machine.bmc.username
            password = self.machine.bmc.password
        elif fence.device == "rpower_device":
            username = self.remote_power_device.username
            password = self.remote_power_device.password

        if not username:
            username = ServerConfig.objects.by_key('remotepower.default.username')
        if not password:
            password = ServerConfig.objects.by_key('remotepower.default.password')

        if not username:
            raise ValueError("Username not available")

        if not password:
            raise ValueError("Password not available")

        return username, password

    def get_power_address(self):
        logging.debug("getting fence object for %s in get_power_adress", self.fence_name)
        fence = RemotePowerType.from_fence(self.fence_name)
        if fence.device == "bmc":
            return self.machine.bmc.fqdn
        if fence.device == "rpower_device":
            return self.remote_power_device.fqdn
        if fence.device == "hypervisor":
            return self.machine.hypervisor.fqdn

    def __str__(self):
        logging.debug("getting fence object for %s in __str___", self.fence_name)
        fence = RemotePowerType.from_fence(self.fence_name)
        return fence.fence + "@" + fence.device
