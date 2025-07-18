import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator
from django.db import models
from django.template import Context, Template
from django.utils.safestring import SafeString

from .serialconsoletype import SerialConsoleType
from .serverconfig import ServerConfig

if TYPE_CHECKING:
    from orthos2.types import (
        MandatoryMachineOneToOneField,
        MandatorySerialConsoleTypeForeignKey,
    )

logger = logging.getLogger("models")


class SerialConsole(models.Model):

    BAUD_RATE_CHOICES = (
        (2400, "2400"),
        (4800, "4800"),
        (9600, "9600"),
        (19200, "19200"),
        (38400, "38400"),
        (57600, "57600"),
        (115200, "115200"),
    )

    # Predefine some and add more if needed
    TTY_CHOICES = (
        ("ttyS", "ttyS"),
        ("ttyUSB", "ttyUSB"),
        ("ttyAMA", "ttyAMA"),
        ("hvc", "hvc"),
        ("None", "None"),
    )

    class Meta:  # type: ignore
        verbose_name = "Serial Console"

    machine: "MandatoryMachineOneToOneField" = models.OneToOneField(
        "data.Machine", on_delete=models.CASCADE, primary_key=True
    )

    console_server: "models.CharField[Optional[str], Optional[str]]" = models.CharField(
        max_length=1024,
        verbose_name="Dedicated console server",
        blank=True,
        null=True,
        help_text="DNS resolvable hostname (FQDN) to serial console server",
    )

    stype: "MandatorySerialConsoleTypeForeignKey" = models.ForeignKey(
        SerialConsoleType,
        verbose_name="Serial Console Type",
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        help_text="Mechanism how to set up and retrieve serial console data",
    )

    port: "models.SmallIntegerField[Optional[int], Optional[int]]" = models.SmallIntegerField(
        null=True,
        blank=True,
        help_text="On which physical port of the Dedicated Console Server is this machine connected?",
    )

    command: "models.CharField[Optional[str], Optional[str]]" = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="Use this with the 'command' type. Template matching applies.",
    )

    rendered_command: "models.CharField[Optional[str], Optional[str]]" = models.CharField(
        max_length=1024,
        null=True,
        blank=True,
        help_text="Final command which is constructed using above info and synced to cscreen server"
        " /etc/cscreenrc config",
    )

    comment: "models.CharField[Optional[str], Optional[str]]" = models.CharField(
        max_length=200,
        null=True,
        blank=True,
    )

    baud_rate: "models.IntegerField[int, int]" = models.IntegerField(
        choices=BAUD_RATE_CHOICES,
        default=57600,
    )

    kernel_device: "models.CharField[str, str]" = models.CharField(
        choices=TTY_CHOICES,
        verbose_name="Kernel Device",
        max_length=64,
        null=False,
        default="ttyS",
        help_text="The kernel device string as passed via kernel command line, e.g. ttyS, ttyAMA, ttyUSB,..."
        ' "None" will remove console= kernel paramter',
    )

    kernel_device_num: "models.PositiveSmallIntegerField[int, int]" = models.PositiveSmallIntegerField(
        null=False,
        validators=[MaxValueValidator(1024)],
        default=0,
        verbose_name="Kernel Device number",
        help_text="""The kernel device number is concatenated to the kernel device string (see above).
A value of 1 might end up in console=ttyS1 kernel command line paramter.""",
    )

    def __str__(self) -> str:
        return self.stype.name

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.clean()
        self.rendered_command = self.get_command_record()
        if self.stype:
            super(SerialConsole, self).save(*args, **kwargs)
        else:
            raise ValidationError("No serial console type set!")

    def clean(self) -> None:
        errors: List[Union[ValidationError, str]] = []

        if not hasattr(self, "stype"):
            return

        if self.stype.name == "Device":
            if self.kernel_device == "None":
                errors.append(
                    ValidationError(
                        "Please provide a kernel device (e.g. '/dev/ttyS123')!"
                    )
                )

            if not self.baud_rate:
                errors.append(ValidationError("Please provide a baud rate!"))

            # requires: device, baud_rate
            self.command = ""
            self.console_server = None
            self.port = None

        elif self.stype.name == "Telnet":
            if not self.console_server:
                errors.append(
                    ValidationError("Please provide a dedicated console server!")
                )

            if not self.port:
                errors.append(ValidationError("Please provide a port!"))

            # requires: console_server, port
            self.command = ""

        elif self.stype.name == "Command":
            if not self.command:
                errors.append(ValidationError("Please provide a command!"))

        elif self.stype.name == "PowerPC HMC":
            self.kernel_device = "hvc"

        elif self.stype.name == "s390":
            if not self.console_server:
                errors.append(
                    ValidationError("Please provide a dedicated console server!")
                )

            # requires: console server
            self.command = ""
            self.device = ""
            self.port = None

        elif self.stype.name in {"IPMI"}:
            if not self.machine.has_bmc():
                errors.append(
                    ValidationError(
                        "Please add a BMC to the machine [%s]" % self.machine.fqdn
                    )
                )

            # requires: management interface
            self.command = ""
            self.console_server = None
            self.port = None

        elif self.stype.name in {"libvirt/qemu", "libvirt/lxc"}:
            if not self.machine.hypervisor:
                errors.append(
                    ValidationError("No hypervisor found [%s]" % self.machine.fqdn)
                )

            # requires: -
            self.command = ""
            self.console_server = None
            self.port = None

        if errors:
            raise ValidationError(errors)

    def get_command_record(self) -> SafeString:
        """Return cscreen record for serial console."""
        prefix = 'screen -t {{ machine.hostname|ljust:"20" }} -L '
        template = self.stype.command

        if template is None:
            raise ValueError("Template for serial console type not set!")

        username = ServerConfig.get_server_config_manager().by_key(
            "serialconsole.ipmi.username", ""
        )
        password = ServerConfig.get_server_config_manager().by_key(
            "serialconsole.ipmi.password", ""
        )

        if username is None or password is None:
            raise ValueError(
                "Username or Password cannot be None to render serial command record!"
            )

        ipmi: Dict[str, str] = {"user": username, "password": password}

        bmc = None
        if self.machine.has_bmc():
            bmc = self.machine.bmc
            if bmc.username:
                ipmi["user"] = bmc.username
            if bmc.password:
                ipmi["password"] = bmc.password

        context = Context(
            {
                "machine": self.machine,
                "bmc": bmc,
                "ipmi": ipmi,
                "kernel_device": self.kernel_device,
                "kernel_device_num": self.kernel_device_num,
                "baud_rate": self.baud_rate,
                "command": self.command,
                "port": self.port,
                "console_server": self.console_server,
            }
        )
        # Render the template twice, to support templates in the command string, which
        # is a template argument itself
        return Template(Template(prefix + template).render(context)).render(context)

    def get_comment_record(self) -> SafeString:
        """Return cscreen comment for serial console."""
        comment = 'defhstatus "{{ comment }}"'
        context = Context(
            {
                "comment": self.comment if self.comment else self.stype.comment,
            }
        )
        return Template(comment).render(context)
