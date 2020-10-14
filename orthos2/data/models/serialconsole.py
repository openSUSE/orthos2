import logging

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.template import Context, Template
from taskmanager import tasks
from taskmanager.models import TaskManager

from . import validate_dns
from .serialconsoletype import SerialConsoleType
from .serverconfig import ServerConfig

logger = logging.getLogger('models')


class CscreenManager(models.Manager):

    def get(self, cscreen_server):
        query = super(CscreenManager, self).get_queryset().filter(
            cscreen_server=cscreen_server
        ).order_by('machine__fqdn')

        return query


class SerialConsole(models.Model):

    BAUD_RATE_CHOICES = (
        (2400, '2400'),
        (4800, '4800'),
        (9600, '9600'),
        (19200, '19200'),
        (38400, '38400'),
        (57600, '57600'),
        (115200, '115200')
    )

    class Meta:
        verbose_name = 'Serial Console'

    machine = models.OneToOneField(
        'data.Machine',
        on_delete=models.CASCADE,
        primary_key=True
    )

    management_bmc = models.ForeignKey(
        'data.Machine',
        verbose_name='Management BMC',
        related_name='managed_serialconsole',
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )

    console_server = models.ForeignKey(
        'data.Machine',
        verbose_name='Dedicated console server',
        related_name='console_server',
        on_delete=models.CASCADE,
        limit_choices_to={'administrative': True},
        blank=True,
        null=True
    )

    type = models.ForeignKey(
        SerialConsoleType,
        on_delete=models.CASCADE,
        null=False,
        blank=False
    )

    device = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    port = models.SmallIntegerField(
        null=True,
        blank=True
    )

    command = models.CharField(
        max_length=200,
        null=True,
        blank=True
    )

    comment = models.CharField(
        max_length=200,
        null=True,
        blank=True
    )

    baud_rate = models.IntegerField(
        choices=BAUD_RATE_CHOICES,
        default=57600
    )

    cscreen_server = models.ForeignKey(
        'data.Machine',
        verbose_name='CScreen server',
        related_name='+',
        on_delete=models.CASCADE,
        limit_choices_to={'administrative': True},
        null=False,
        blank=False
    )

    kernel_device = models.SmallIntegerField(
        null=False,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(1024)
        ],
        default=0
    )

    updated = models.DateTimeField(
        'Updated at',
        auto_now=True
    )

    created = models.DateTimeField(
        'Created at',
        auto_now_add=True
    )

    objects = models.Manager()
    cscreen = CscreenManager()

    def __str__(self):
        return self.type.name

    def save(self, *args, **kwargs):
        self.clean()

        if not self.cscreen_server.administrative:
            raise ValidationError(
                "CScreen server '{}' must be administrative!".format(self.cscreen_server)
            )

        if self.type:
            super(SerialConsole, self).save(*args, **kwargs)
        else:
            raise ValidationError("No serial console type set!")

    def clean(self):
        errors = []

        if not hasattr(self, 'type'):
            return

        if self.type.name == 'Device':
            if not self.device:
                errors.append(ValidationError("Please provide a device (e.g. '/dev/ttyS123')!"))

            if not self.baud_rate:
                errors.append(ValidationError("Please provide a baud rate!"))

            # requires: device, baud_rate
            self.command = ''
            self.console_server = None
            self.management_bmc = None
            self.port = None

        elif self.type.name == 'Telnet':
            if not self.console_server:
                errors.append(ValidationError("Please provide a dedicated console server!"))

            if not self.port:
                errors.append(ValidationError("Please provide a port!"))

            # requires: console_server, port
            self.command = ''
            self.device = ''
            self.management_bmc = None

        elif self.type.name == 'Command':
            if not self.command:
                errors.append(ValidationError("Please provide a command!"))

            # requires: command
            self.device = ''
            self.console_server = None
            self.port = None
            self.management_bmc = None

        elif self.type.name == 's390':
            if not self.console_server:
                errors.append(ValidationError("Please provide a dedicated console server!"))

            # requires: console server
            self.command = ''
            self.device = ''
            self.port = None
            self.management_bmc = None

        elif self.type.name in {'IPMI', 'ILO', 'ILO2'}:
            if not self.machine.bmc:
                errors.append(ValidationError("Please add at least one BMC to the enclosure!"))

            if not self.management_bmc:
                errors.append(ValidationError("Please select a management BMC!"))

            # requires: management interface
            self.command = ''
            self.device = ''
            self.console_server = None
            self.port = None

        elif self.type.name in {'libvirt/qemu', 'libvirt/lxc'}:
            if not self.machine.hypervisor:
                errors.append(ValidationError("No hypervisor found!"))

            # requires: -
            self.command = ''
            self.device = ''
            self.console_server = None
            self.port = None
            self.management_bmc = None

        if errors:
            raise ValidationError(errors)

    def get_command_record(self):
        """Return cscreen record for serial console."""
        prefix = 'screen -t {{ machine.hostname|ljust:"20" }} -L '
        template = self.type.command

        username = ServerConfig.objects.by_key('serialconsole.ipmi.username')
        password = ServerConfig.objects.by_key('serialconsole.ipmi.password')

        if username is None or password is None:
            return

        ipmi = {'user': username, 'password': password}

        context = Context({
            'machine': self.machine,
            'ipmi': ipmi,
            'device': self.device,
            'baud_rate': self.baud_rate,
            'command': self.command,
            'port': self.port,
            'console_server': self.console_server
        })

        return Template(prefix + template).render(context)

    def get_comment_record(self):
        """Return cscreen comment for serial console."""
        comment = 'defhstatus "{{ comment }}"'
        context = Context({
            'comment': self.comment if self.comment else self.type.comment,
        })
        return Template(comment).render(context)
