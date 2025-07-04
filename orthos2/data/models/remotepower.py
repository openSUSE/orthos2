import logging
from typing import TYPE_CHECKING, Any, List, Optional, Tuple

from django.core.exceptions import ValidationError
from django.db import models

from orthos2.data.models.serverconfig import ServerConfig

if TYPE_CHECKING:
    from orthos2.data.models.remotepowertype import RemotePowerType
    from orthos2.types import (
        MandatoryMachineOneToOneField,
        OptionalRemotePowerDeviceForeignKey,
        OptionalRemotePowerTypeForeignKey,
    )


class RemotePower(models.Model):
    class Action:
        ON = "on"
        OFF = "off"
        OFF_SSH = "off-ssh"
        OFF_REMOTEPOWER = "off-remotepower"
        REBOOT = "reboot"
        REBOOT_SSH = "reboot-ssh"
        REBOOT_REMOTEPOWER = "reboot-remotepower"
        STATUS = "status"

        as_list = [
            ON,
            OFF,
            REBOOT,
            STATUS,
            OFF_SSH,
            OFF_REMOTEPOWER,
            REBOOT_SSH,
            REBOOT_REMOTEPOWER,
        ]

    class Status:
        UNKNOWN = 0
        ON = 1
        OFF = 2
        BOOT = 3
        SHUTDOWN = 4
        PAUSED = 5

        @classmethod
        def to_str(cls, index: int) -> str:
            return {
                cls.UNKNOWN: "unknown",
                cls.ON: "on",
                cls.OFF: "off",
                cls.BOOT: "boot",
                cls.SHUTDOWN: "shut down",
                cls.PAUSED: "paused",
            }.get(index, "undefined")

    fence_agent: "OptionalRemotePowerTypeForeignKey" = models.ForeignKey(
        "data.RemotePowerType",
        on_delete=models.CASCADE,
        verbose_name="Fence Agent",
        null=True,
    )

    machine: "MandatoryMachineOneToOneField" = models.OneToOneField(
        "data.Machine", on_delete=models.CASCADE, primary_key=True
    )

    remote_power_device: "OptionalRemotePowerDeviceForeignKey" = models.ForeignKey(
        "data.RemotePowerDevice",
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )

    port: "models.CharField[Optional[str], Optional[str]]" = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    comment: "models.CharField[Optional[str], Optional[str]]" = models.CharField(
        max_length=200,
        null=True,
        blank=True,
    )

    options: "models.CharField[str, str]" = models.CharField(
        max_length=1024,
        blank=True,
        default="",
        help_text="""Additional command line options to be passed to the fence agent.
        E. g. "managed=<management LPAR> for lpar""",
    )

    def clean_fence_agent(self) -> None:
        """
        Validate the fence_agent field to ensure it is of type "hypervisor".
        This method is called automatically by Django's validation system.
        """
        if not self.fence_agent:
            raise ValidationError("Fence name cannot be empty.")
        if self.fence_agent.device != "hypervisor":
            raise ValidationError(
                "The fence agent must be of type 'hypervisor'. "
                "Please select a valid fence agent."
            )

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Check values before saving the remote power object. Do only save if type is set."""

        errors: List[ValidationError] = []
        fence = self.get_remotepower_fence()
        if fence.device == "rpower_device":
            if fence.use_port:
                if self.port is None:  # test for None, as port may be 0
                    errors.append(ValidationError("Please provide a port!"))
            elif fence.use_hostname_as_port:
                self.port = self.machine.hostname
            else:
                self.port = None
            if self.remote_power_device:
                self.fence_agent = self.remote_power_device.fence_agent
            else:
                errors.append(ValidationError("Please provide a remote power device!"))
        elif fence.device == "bmc":
            if self.machine.bmc:
                self.fence_agent = self.machine.bmc.fence_agent
                self.remote_power_device = None
            else:
                errors.append(
                    ValidationError("The machine needs to have an associated BMC")
                )

        elif fence.device == "hypervisor":
            if self.machine.hypervisor:
                self.remote_power_device = None
            else:
                errors.append(ValidationError("No hypervisor found!"))

        else:
            errors.append(
                ValidationError(
                    "{} is not a valid switching device".format(
                        fence["switching_device"]  # type: ignore
                    )
                )
            )

        if errors:
            raise ValidationError(errors)

        # check for `None` explicitly because type 0 results in false
        if self.fence_agent is not None:  # type: ignore
            super(RemotePower, self).save(*args, **kwargs)
        else:
            raise ValidationError("No remote power type set!")

    def get_remotepower_fence(self) -> "RemotePowerType":
        """
        Get the fence agent for the remote power object. This is giving you either the directly set fence agent, the
        remote power device fence agent or the BMC fence agent.

        :returns: The fence agent for the remote power object
        :raises ValueError: If no fence agent is set for the remote power object
        """
        if self.fence_agent:
            return self.fence_agent
        if self.remote_power_device:
            return self.remote_power_device.fence_agent
        if self.machine.bmc:
            return self.machine.bmc.fence_agent
        raise ValueError("No fence agent set for remote power object. Invalid state!")

    @property
    def name(self) -> Optional[str]:
        if self.fence_agent is None:
            return None
        return self.fence_agent.device

    def power_on(self) -> None:
        """Power on the machine."""
        self._perform("on")

    def power_off(self) -> None:
        """Power off the machine."""
        self._perform("off")

    def reboot(self) -> None:
        """Reboot the machine."""
        self._perform("reboot")

    def get_status(self) -> int:
        """Return the current power status."""
        result = self._perform("status")
        if not result:
            raise RuntimeError("recieved no result from _perform('status')")

        if result.lower().find("failed to execute power task on") > -1:
            status = self.Status.UNKNOWN
        elif result.lower().find("status: off") > -1:
            status = self.Status.OFF
        elif result.lower().find("status: on") > -1:
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
        server = CobblerServer(self.machine.fqdn_domain)
        if server:
            result = server.powerswitch(self.machine, action)
        return result

    def get_credentials(self) -> Tuple[str, str]:
        """
        Return username and password for a login on the switching device
        Use Values from the approrpriate device object, If they don't exist
        fall back to the server config. If that does not exist either, raise an
        exception.
        Returns a Tuple (username, password)
        """
        password = None
        username = None
        fence = self.fence_agent
        if not fence:
            raise ValueError("No fence agent set for remote power object")
        if fence.device == "bmc":
            username = self.machine.bmc.username
            password = self.machine.bmc.password
        elif fence.device == "rpower_device":
            if self.remote_power_device is None:
                raise ValueError("No remote power device set for this machine")
            username = self.remote_power_device.username
            password = self.remote_power_device.password

        if not username:
            username = ServerConfig.get_server_config_manager().by_key(
                "remotepower.default.username"
            )
        if not password:
            password = ServerConfig.get_server_config_manager().by_key(
                "remotepower.default.password"
            )

        if not username:
            raise ValueError("Username not available")

        if not password:
            raise ValueError("Password not available")

        return username, password

    def get_power_address(self) -> Optional[str]:
        fence = self.get_remotepower_fence()
        if fence.device == "bmc":
            return self.machine.bmc.fqdn
        if fence.device == "rpower_device":
            if self.remote_power_device is None:
                raise ValueError("No remote power device set for this machine")
            return self.remote_power_device.fqdn
        if fence.device == "hypervisor":
            if self.machine.hypervisor is None:
                raise ValueError("No hypervisor set for this machine")
            return self.machine.hypervisor.fqdn
        return None

    def __str__(self) -> str:
        logging.debug("getting fence object for %s in __str___", self.machine.fqdn)
        fence = self.get_remotepower_fence()
        return fence.name + "@" + fence.device
