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

from utils.misc import execute, get_s390_hostname
from utils.ssh import SSH

from . import ServerConfig, System, validate_dns

logger = logging.getLogger('models')


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

    class Type:
        TELNET = 0
        SENTRY = 1
        ILO = 2
        IPMI = 3
        DOMINIONPX = 4
        LIBVIRTQEMU = 5
        LIBVIRTLXC = 6
        WEBCURL = 7
        S390 = 8

        @classmethod
        def to_str(cls, index):
            """Return type as string (remote power type name) by index."""
            for type_tuple in RemotePower.TYPE_CHOICES:
                if int(index) == type_tuple[0]:
                    return type_tuple[1]
            raise Exception("Remote power type with ID '{}' doesn't exist!".format(index))

        @classmethod
        def to_int(cls, name):
            """Return type as integer if name matches."""
            for type_tuple in RemotePower.TYPE_CHOICES:
                if name.lower() == type_tuple[1].lower():
                    return type_tuple[0]
            raise Exception("Remote power type '{}' not found!".format(name))

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

    TYPE_CHOICES = (
        (Type.TELNET, 'Telnet'),
        (Type.SENTRY, 'Sentry'),
        (Type.ILO, 'ILO'),
        (Type.IPMI, 'IPMI'),
        (Type.DOMINIONPX, 'Dominion PX'),
        (Type.LIBVIRTQEMU, 'libvirt/qemu'),
        (Type.LIBVIRTLXC, 'libvirt/lxc'),
        (Type.WEBCURL, 'WEBcurl'),
        (Type.S390, 's390')
    )

    def limit_remote_power_device_choices():
        """
        Allow only devices of type remote power.

        This needs to be in callable form because of later assignment of the type variable.
        """
        return {'system': System.Type.REMOTEPOWER}

    machine = models.OneToOneField(
        'data.Machine',
        on_delete=models.CASCADE,
        primary_key=True
    )

    type = models.SmallIntegerField(
        choices=TYPE_CHOICES,
        blank=False,
        null=False,
    )

    management_bmc = models.ForeignKey(
        'data.Machine',
        verbose_name='Management BMC',
        related_name='managed_remotepower',
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )

    remote_power_device = models.ForeignKey(
        'data.Machine',
        related_name='+',
        limit_choices_to=limit_remote_power_device_choices,
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )

    port = models.SmallIntegerField(
        null=True,
        blank=True
    )

    device = models.SmallIntegerField(
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

    def __init__(self, *args, **kwargs):
        """
        Cast plain `RemotePower` object to respective subclass.

        Subclasses getting collected automatically by inheritance of `RemotePower` class.
        """
        subclasses = {
            sub.__name__.replace(self.__class__.__name__, '').lower(): sub
            for sub in self.__class__.__subclasses__()
        }
        self._remotepowertypes = dict(
            map(lambda x: (
                x[0], {
                    'class': subclasses[x[1].lower().replace(' ', '').replace('/', '')],
                    'name': x[1]
                }), self.TYPE_CHOICES)
        )
        super(RemotePower, self).__init__(*args, **kwargs)

    def _set_remotepowertype(self, type):
        """Set remote power type."""
        self.__class__ = self._remotepowertypes[type]['class']

    def __setattr__(self, attr, value):
        """If `type` attribute changes, set respective subclass."""
        # check for `None` explicitly because type 0 results in false
        if attr == 'type' and value is not None:
            self._set_remotepowertype(value)
        super(RemotePower, self).__setattr__(attr, value)

    def __str__(self):
        if self.type is None:
            return 'None'
        return '{}@{}'.format(self.name, self.machine.fqdn)

    def save(self, *args, **kwargs):
        """Check values before saving the remote power object. Do only save if type is set."""
        self.clean()

        if self.remote_power_device:
            if self.remote_power_device.system_id != System.Type.REMOTEPOWER:
                raise ValidationError(
                    (
                        "Remote power device '{}' must have system type 'REMOTEPOWER'!".format(
                            self.remote_power_device
                        )
                    )
                )

        # check for `None` explicitly because type 0 results in false
        if self.type is not None:
            super(RemotePower, self).save(*args, **kwargs)
        else:
            raise ValidationError("No remote power type set!")

    def clean(self):
        """
        Check for every remote power type if all required fields are set and deletes unutilized
        values.
        """
        errors = []

        if self.type in {self.Type.TELNET, self.Type.DOMINIONPX}:
            if not self.remote_power_device:
                errors.append(ValidationError("Please provide a remote power device!"))

            if self.port is None:
                errors.append(ValidationError("Please provide a port!"))

            # requires: remote_power_device, port
            self.device = None
            self.management_bmc = None

        elif self.type in {self.Type.SENTRY, self.Type.S390}:
            if not self.remote_power_device:
                errors.append(ValidationError("Please provide a remote power device!"))

            # requires: remote_power_device
            self.device = None
            self.management_bmc = None
            self.port = None

        elif self.type in {self.Type.ILO, self.Type.IPMI, self.Type.WEBCURL}:
            if not self.machine.bmc:
                errors.append(ValidationError("Please add at least one BMC to the enclosure!"))

            if not self.management_bmc:
                errors.append(ValidationError("Please select a management BMC!"))

            # requires: management_bmc
            self.device = None
            self.port = None
            self.remote_power_device = None

        elif self.type in {self.Type.LIBVIRTQEMU, self.Type.LIBVIRTLXC}:
            if not self.machine.hypervisor:
                errors.append(ValidationError("No hypervisor found!"))

            # requires: -
            self.device = None
            self.management_bmc = None
            self.port = None
            self.remote_power_device = None

        if self.machine.system == System.Type.LPAR_ZSERIES and self.type != self.Type.S390:
            errors = [
                (ValidationError(
                    "Combination of machine system and selected remote power type is not valid!"
                ))
            ]

        if self.machine.system == System.Type.KVM_VM and self.type != self.Type.LIBVIRTQEMU:
            errors = [
                (ValidationError(
                    "Combination of machine system and selected remote power type is not valid!"
                ))
            ]

        if errors:
            raise ValidationError(errors)

    @property
    def name(self):
        if self.type is None:
            return None
        return self.Type.to_str(self.type)

    def power_on(self):
        """Power on the machine."""
        self._perform('on')

    def power_off(self):
        """Power off the machine."""
        self._perform('off')

    def reboot(self):
        """Reboot the machine."""
        logger.warning("Not implemented: {}".format(self))

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

    def get_credentials(self, remotepower_type=None, password_only=False):
        """
        Return username and password for remotepower login.

        Check for specific remotepower type if given, use default password/username if no DB entry
        exists. If no password/username can be found, an exception gets raised.

        The return type is a tuple: (<password>, <username>)
        """
        password = None
        username = None

        if remotepower_type is not None:
            password = ServerConfig.objects.by_key(
                'remotepower.{}.password'.format(remotepower_type)
            )

        if not password:
            password = ServerConfig.objects.by_key('remotepower.default.password')
            if not password:
                raise Exception(
                    "No login password available for {}".format(remotepower_type.upper())
                )

        if password_only:
            return (password, None)

        if remotepower_type is not None:
            username = ServerConfig.objects.by_key(
                'remotepower.{}.username'.format(remotepower_type)
            )

        if not username:
            username = ServerConfig.objects.by_key('remotepower.default.username')
            if not username:
                raise Exception(
                    "No login user available for {}".format(remotepower_type.upper())
                )

        return (password, username)


class Telnet(RemotePower):

    class Meta:
        proxy = True
        verbose_name = 'Remote Power'

    def _perform(self, action):
        """Common implementation for on, off and reset."""
        result = False

        password, username = self.get_credentials('telnet', password_only=True)

        tn = telnetlib.Telnet(self.remote_power_device.fqdn)
        tn.read_until(b"Enter Password: ")
        tn.write("{}\r\n".format(password).encode())
        tn.read_until(b"NPS> ")
        if action == 'status':
            tn.write(br"/S\r\n")
            status = tn.read_until(b"NPS> ")
        else:
            tn.write("/{} {}\r\n".format(action, self.port).encode())
            tn.read_until(b"Sure? (Y/N): ")
            tn.write(b"y\r\n")
            tn.read_until(b"NPS> ")
        tn.write(b"/x\r\n")
        tn.read_until(b"Sure? (Y/N): ")
        tn.write(b"y\r\n")

        tn.close()
        result = True

        if action == 'status':
            return status.splitlines()[5 + self.port].decode('utf-8').strip('\n')[28:31]

        return result

    def reboot(self):
        """Reboot the machine."""
        self._perform('Boot')


class Sentry(RemotePower):

    class Meta:
        proxy = True
        verbose_name = 'Remote Power'

    def _perform(self, action):
        """Common implementation for on, off and reset."""
        result = False

        password, username = self.get_credentials('sentry')

        tn = telnetlib.Telnet(self.remote_power_device.fqdn)
        output = tn.read_until(b"Username: ")

        # Sentry Switched PDU Version 8.0g
        result = re.search(br"Sentry Switched [CP]DU Version (\d+)\.(\d+)", output)
        try:
            major_version = int(result.group(1))
            minor_version = int(result.group(2))
        except Exception:
            raise Exception(
                "Can't detect firmware version: {}".format(self.remote_power_device.fqdn)
            )

        tn.write("{}\r\n".format(username).encode())
        tn.read_until(b"Password: ")
        tn.write("{}\r\n".format(password).encode())
        tn.expect([b"Switched [CP]DU: "])
        if action == 'status':
            tn.write("status {}\r\n".format(self.machine.hostname).encode())
            output = tn.expect([b"Switched [CP]DU: "])[2].decode()
        else:
            tn.write("{} {}\r\n".format(action, self.machine.hostname).encode())
            tn.expect([b"Switched [CP]DU: "])
        tn.write(b"exit\r\n")

        tn.close()
        result = True

        if action == 'status':
            if major_version == 7:
                # Outlet   Outlet                    Outlet     Control
                # ID       Name                      Status     Status
                # .AB3     <hostname>                On         On
                result = re.search(r"{}[ ]+(\w+)".format(self.machine.hostname), output)
                if result:
                    return result.group(1)
            elif major_version == 8:
                # ID    Outlet Name                      Control State  State  Status
                # --    -----------                      -------------  -----  ------
                # AA7   <hostname>                       On             On     Normal
                result = re.search(r"{}[ ]+\w+[ ]*(\w+)".format(self.machine.hostname), output)
                if result:
                    return result.group(1)
            else:
                logger.warning(
                    "Unknown Sentry FW version '{}.{}' on: {}".format(
                        major_version,
                        minor_version,
                        self.remote_power_device.fqdn
                    )
                )
                return self.Status.UNKNOWN

        return result

    def reboot(self):
        """Reboot the machine."""
        self._perform('Boot')


class ILO(RemotePower):

    class Meta:
        proxy = True
        verbose_name = 'Remote Power'

    def _perform(self, action):
        """Common implementation for on, off and reset."""
        result = False

        password, username = self.get_credentials('ilo')

        if not self.machine.bmc:
            logger.error("No management interface found")
            raise Exception("No hypervisor found")

        tn = telnetlib.Telnet(self.machine.bmc.fqdn)
        tn.read_until(b"Login Name: ")
        tn.write("{}\r\n".format(username).encode())
        tn.read_until(b"Password: ")
        tn.write("{}\r\n".format(password).encode())
        tn.read_until(b"</>hpiLO-> ")
        if action == 'status':
            tn.write(b"power\r\n")
            status = tn.read_until(b"</>hpiLO-> ")
        else:
            tn.write("{} system1\r\n".format(action).encode())
            tn.read_until(b"</>hpiLO-> ")
        tn.write(b"exit\r\n")

        tn.close()
        result = True

        if action == 'status':
            return status.splitlines()[2].decode('utf-8').strip('\n')[34:]

        return result

    def power_on(self):
        """Power on the machine."""
        self._perform('start')

    def power_off(self):
        """Power off the machine."""
        self._perform('stop')

    def reboot(self):
        """Reboot the machine."""
        self._perform('reset')


class IPMI(RemotePower):

    class Meta:
        proxy = True
        verbose_name = 'Remote Power'

    def _perform(self, action):
        """Common implementation for on, off and reset."""
        result = False

        password, username = self.get_credentials('ipmi')

        template = ServerConfig.objects.by_key('remotepower.ipmi.command')
        if template is None:
            return

        ipmi = {'user': username, 'password': password}

        context = Context({
            'machine': self.machine,
            'ipmi': ipmi,
            'action': action
        })

        command = Template(template).render(context)
        stdout, stderr, exitstatus = execute(command)
        result = True

        if action == 'status':
            if exitstatus == 0:
                return stdout
            else:
                return self.Status.UNKNOWN

        if exitstatus != 0:
            raise Exception(''.join(stderr))

        return result

    def reboot(self):
        """Reboot the machine."""
        status = self._perform('status')

        if 'off' in status.lower():
            self._perform('on')
        else:
            self._perform('off')
            time.sleep(5)
            self._perform('on')


class DominionPX(RemotePower):

    class Meta:
        proxy = True
        verbose_name = 'Remote Power'

    def _perform(self, action):
        """Common implementation for on, off and reset."""
        result = False

        password, username = self.get_credentials('dominionpx')

        tn = telnetlib.Telnet(self.remote_power_device.fqdn)
        tn.read_until(b"Login: ")
        tn.write("{}\r\n".format(username).encode())
        tn.read_until(b"Password: ")
        tn.write("{}\r\n".format(password).encode())
        tn.read_until(b"clp:/-> ")
        if action == 'status':
            tn.write("show /system1/outlet{}\r\n".format(self.port).encode())
            status = tn.read_until(b"clp:/-> ")
        else:
            tn.write("set /system1/outlet{} powerState={}\r\n".format(
                self.port,
                action
            ).encode())

            tn.read_until(b"clp:/-> ")
        tn.write(b"exit\r\n")

        tn.close()
        result = True

        if action == 'status':
            return status.splitlines()[4][2:].decode('utf-8').strip('\n')

        return result

    def reboot(self):
        """Reboot the machine."""
        self._perform('off')
        time.sleep(8)
        self._perform('on')


class LibvirtQEMU(RemotePower):

    class Meta:
        proxy = True
        verbose_name = 'Remote Power'

    def _perform(self, action):
        """Common implementation for on, off and reset."""
        name = self.machine.hostname
        virsh = 'virsh -c qemu:///system'
        conn = None
        result = False

        if not self.machine.hypervisor.fqdn:
            logger.error("No hypervisor system found")
            raise Exception("No hypervisor found")

        conn = SSH(self.machine.hypervisor.fqdn)
        conn.connect()

        if action == 'status':

            stdout, stderr, exitstatus = conn.execute('{} list --all'.format(virsh))

            if exitstatus != 0:
                logger.error(''.join(stderr))
                raise Exception(''.join(stderr))

            for line in stdout[2:]:
                columns = line.strip().split()

                if columns[1] == name:
                    return {
                        'running': self.Status.ON,
                        'shut': self.Status.OFF,
                        'paused': self.Status.PAUSED
                    }.get(columns[2], 0)

            raise Exception("Couldn't find domain '{}'!".format(name))

        elif action == 'off':
            stdout, stderr, exitstatus = conn.execute('{} destroy {}'.format(virsh, name))

            if exitstatus == 0:
                logger.debug("Virtual machine '{}' stopped".format(name))
                result = True
            else:
                logger.error(''.join(stderr))
                raise Exception(''.join(stderr))

        elif action == 'on':
            stdout, stderr, exitstatus = conn.execute('{} start {}'.format(virsh, name))

            if exitstatus == 0:
                logger.debug("Virtual machine '{}' started".format(name))
                result = True
            else:
                logger.error(''.join(stderr))
                raise Exception(''.join(stderr))

        else:
            logger.warning("Action '{}' does not exist".format(action))
            result = False

        if conn:
            conn.close()

        return result

    def reboot(self):
        """Reboots the machine."""
        self._perform('off')
        time.sleep(5)
        self._perform('on')


class LibvirtLXC(RemotePower):

    class Meta:
        proxy = True
        verbose_name = 'Remote Power'

    def _perform(self, action):
        """Common implementation for on, off and reset."""
        name = self.machine.hostname
        virsh = 'virsh -c lxc:///'
        conn = None
        result = False

        if not self.machine.hypervisor.fqdn:
            logger.error("No hypervisor system found")
            raise Exception("No hypervisor found")

        conn = SSH(self.machine.hypervisor.fqdn)
        conn.connect()

        if action == 'status':

            stdout, stderr, exitstatus = conn.execute('{} list --all'.format(virsh))

            if exitstatus != 0:
                logger.error(''.join(stderr))
                raise Exception(''.join(stderr))

            for line in stdout[2:]:
                columns = line.strip().split()

                if columns[1] == name:
                    return {
                        'running': self.Status.ON,
                        'shut': self.Status.OFF,
                        'paused': self.Status.PAUSED
                    }.get(columns[2], 0)

            raise Exception("Couldn't find domain '{}'!".format(name))

        elif action == 'off':
            stdout, stderr, exitstatus = conn.execute('{} destroy {}'.format(virsh, name))

            if exitstatus == 0:
                logger.debug("Virtual machine '{}' stopped".format(name))
                result = True
            else:
                logger.error(''.join(stderr))
                raise Exception(''.join(stderr))

        elif action == 'on':
            stdout, stderr, exitstatus = conn.execute('{} start {}'.format(virsh, name))

            if exitstatus == 0:
                logger.debug("Virtual machine '{}' started".format(name))
                result = True
            else:
                logger.error(''.join(stderr))
                raise Exception(''.join(stderr))

        else:
            logger.warning("Action '{}' does not exist".format(action))
            result = False

        if conn:
            conn.close()

        return result

    def reboot(self):
        """Reboot the machine."""
        self._perform('off')
        time.sleep(5)
        self._perform('on')


class S390(RemotePower):

    class Meta:
        proxy = True
        verbose_name = 'Remote Power'

    def _perform(self, action):
        """Common implementation for on, off and reset."""
        base_url = 'http://zrouter61.suse.de/cgi-bin/'
        orthos = '+ORTHOS'
        name = get_s390_hostname(self.machine.fqdn)
        ipl_device = '+150'
        result = False

        if action == 'status':
            prefix = 'serve-noncgis?'
            url = base_url + prefix + name + orthos

        elif action == 'on':
            prefix = 'guest_start.sh?'
            time = '+150'
            url = base_url + prefix + name + time + orthos

        elif action == 'off':
            prefix = "guest_shutdown.sh?"
            url = base_url + prefix + name + orthos

        elif action == 'install':
            prefix = "guest_install.sh?"
            url = base_url + prefix + name + ipl_device

        else:
            logger.warning("Action '{}' does not exist".format(action))
            return False

        urlsocket = request.urlopen(url)

        result = urlsocket.read()
        result.decode('utf-8').strip('\n')
        result = True

        if action == 'status':
            if int(result) == 1:
                return 'on'
            elif int(result) == 0:
                return 'off'
            else:
                return 'unknown'

        return result

    def reboot(self):
        """Reboot the machine."""
        self._perform('off')
        time.sleep(5)
        self._perform('on')


class WEBCurl(RemotePower):

    class Meta:
        proxy = True
        verbose_name = 'Remote Power'

    def _perform(self, action):
        """Common implementation for on, off and reset."""
        result = False

        password, username = self.get_credentials('webcurl')

        os.system('curl -i http://{}/rack1.html -u "{}:{}" 2>&1'.format(
            self.remote_power_device.fqdn,
            username,
            password
        ))

        if action == 'status':
            status = 'unknown'
        else:
            os.system('curl -i http://{}/rack1.html -u "{}:{}" -d P{}{}={} 2>&1'.format(
                self.remote_power_device.fqdn,
                username,
                password,
                self.device,
                self.port,
                action
            ))
            result = True

        if action == 'status':
            return status

        return result

    def power_on(self):
        """Power on the machine."""
        self._perform(1)

    def power_off(self):
        """Power off the machine."""
        self._perform(0)

    def reboot(self):
        """Reboot the machine."""
        self._perform(0)
        time.sleep(8)
        self._perform(1)
