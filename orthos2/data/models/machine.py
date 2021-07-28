import datetime
import logging
import re
from copy import deepcopy

from orthos2.data.exceptions import ReleaseException, ReserveException
from django.conf import settings
from django.contrib.auth.models import User
from django.core import serializers
from django.core.exceptions import (PermissionDenied, ValidationError)
from django.db import models
from django.db.models import Q
from django.utils import timezone
from orthos2.utils.misc import (Serializer, get_domain, get_hostname,
                                get_ipv4, get_ipv6, get_s390_hostname,
                                is_dns_resolvable)

from .architecture import Architecture
from .domain import Domain, DomainAdmin, validate_domain_ending
from .enclosure import Enclosure
from .machinegroup import MachineGroup
from .networkinterface import validate_mac_address, NetworkInterface
from .platform import Platform
from .system import System
from .virtualizationapi import VirtualizationAPI
from .serverconfig import ServerConfig

logger = logging.getLogger('models')


def validate_dns(value):
    if not is_dns_resolvable(value):
        raise ValidationError("No DNS lookup result for '{}'".format(value))


def check_permission(function):
    """Return decorator for checking machine specific methods."""

    def decorator(machine, *args, **kwargs):
        """
        Check permission:

        - no `user` keyword                                         -> allow
        - is superuser                                              -> allow
        - is groupadmin (`is_privileged`)                           -> allow
        - machine reserved by user                                  -> allow
        - call `reserve` and not reserved and not administrative    -> allow
        - call `release` and not reserved and not administrative    -> allow

        If no `user` keyword argument is given, access is granted (used for server-side call).
        """
        user = kwargs.get('user', None)

        if not user:
            # grant access if no user is given for e.g. a server call
            return function(machine, *args, **kwargs)

        elif user.is_superuser:
            logger.debug(
                "Allow {} of {} by {} (superuser)".format(function.__name__, machine, user)
            )
            return function(machine, *args, **kwargs)

        elif user in User.objects.filter(memberships__group__name=machine.group,
                                         memberships__is_privileged=True):
            logger.debug(
                "Allow {} of {} by {} (privileged user)".format(function.__name__, machine, user)
            )
            return function(machine, *args, **kwargs)

        elif machine.reserved_by == user:
            logger.debug(
                "Allow {} of {} by {} (reservation owner)".format(function.__name__, machine, user)
            )
            return function(machine, *args, **kwargs)

        elif function.__qualname__ == 'Machine.reserve' and not machine.reserved_by and\
                not machine.administrative:
            logger.debug(
                "Allow {} of {} by {} (not reserved)".format(function.__name__, machine, user)
            )
            return function(machine, *args, **kwargs)

        elif function.__qualname__ == 'Machine.release' and not machine.reserved_by and\
                not machine.administrative:
            logger.debug(
                "Allow {} of {} by {} (not reserved)".format(function.__name__, machine, user)
            )
            return function(machine, *args, **kwargs)

        else:
            logger.debug(
                "Deny {} of {} by {}".format(function.__name__, machine, user)
            )
            raise PermissionDenied("You are not allowed to perform this action!")

    return decorator


class RootManager(models.Manager):

    def get_queryset(self):
        """Exclude all inactive machines."""
        queryset = super(RootManager, self).get_queryset()

        return queryset.exclude(active=False)


class ViewManager(RootManager):

    def get_queryset(self, user=None):
        """Exclude administrative machines/systems from all view requested by non-superusers."""
        queryset = super(ViewManager, self).get_queryset()

        if (not user) or (not user.is_superuser):
            queryset = queryset.exclude(administrative=True)
            queryset = queryset.exclude(system__administrative=True)

        return queryset


class SearchManager(ViewManager):

    def form(self, parameters, user=None):
        """Filter machine queryset by advanced search parameters."""
        parameters = {key: value for key, value in parameters.items() if value}

        queryset = super(SearchManager, self).get_queryset(user=user)
        query = None
        for key, value in parameters.items():
            if not key.endswith('__operator'):
                operator = parameters.get('{}__operator'.format(key), '')

                if value == '__True':
                    value = True
                elif value == '__False':
                    value = False

                q = Q(**{'{}{}'.format(key, operator): value})
                if query:
                    query = query & q
                else:
                    query = q

        if query:
            queryset = queryset.filter(query).distinct()
        else:
            queryset = queryset.all()

        return queryset


class Machine(models.Model):

    class Meta:
        ordering = ['fqdn']

    class Connectivity:
        NONE = 0
        PING = 1
        SSH = 2
        ALL = 3

    class StatusIP:
        UNREACHABLE = 0
        REACHABLE = 1
        CONFIRMED = 2
        MAC_MISMATCH = 3
        ADDRESS_MISMATCH = 4
        NO_ADDRESS = 5
        AF_DISABLED = 6

        CHOICE = (
            (UNREACHABLE, 'unreachable'),
            (REACHABLE, 'reachable'),
            (CONFIRMED, 'confirmed'),
            (MAC_MISMATCH, 'MAC mismatch'),
            (ADDRESS_MISMATCH, 'address mismatch'),
            (NO_ADDRESS, 'no address assigned'),
            (AF_DISABLED, 'address-family disabled'),
        )

    CONNECTIVITY_CHOICE = (
        (Connectivity.NONE, 'Disable'),
        (Connectivity.PING, 'Ping only'),
        (Connectivity.SSH, 'SSH (includes Ping+SSH)'),
        (Connectivity.ALL, 'Full (includes Ping+SSH+Login)'),
    )

    enclosure = models.ForeignKey(
        Enclosure,
        blank=True,
        on_delete=models.CASCADE,
        help_text="Enclosure/chassis of one or more machines"
    )

    fqdn = models.CharField(
        'FQDN',
        max_length=200,
        blank=False,
        unique=True,
        validators=[validate_dns, validate_domain_ending],
        db_index=True,
        help_text="The Fully Qualified Domain Name of the main network interface of the machine"
    )

    system = models.ForeignKey(System, on_delete=models.CASCADE)

    comment = models.CharField(
        max_length=512,
        blank=True,
        help_text="Machine specific problems or extras you want to tell others?"
    )

    serial_number = models.CharField(
        max_length=200,
        blank=True,
        help_text="The serial number can be read from a sticker on the machine's chassis (e.g. GPDRDP5022003)"
    )

    product_code = models.CharField(
        max_length=200,
        blank=True,
        help_text="The product code can be read from a sticker on the machine's chassis (e.g. S1DL1SEXA)"
    )

    architecture = models.ForeignKey(Architecture, on_delete=models.CASCADE)

    fqdn_domain = models.ForeignKey(
        Domain,
        on_delete=models.CASCADE,
        help_text="The domain name of the primary NIC"
    )

    cpu_model = models.CharField(
        'CPU model',
        max_length=200,
        blank=True,
        help_text="The domain name of the primary NIC"
    )

    cpu_flags = models.TextField(
        'CPU flags',
        blank=True,
        help_text="CPU feature/bug flags as exported from the kernel (/proc/cpuinfo)"
    )

    cpu_physical = models.IntegerField(
        'CPU sockets',
        default=1
    )

    cpu_cores = models.IntegerField(
        'CPU cores',
        default=1,
        help_text="Amount of CPU cores"
    )

    cpu_threads = models.IntegerField(
        'CPU threads',
        default=1,
        help_text="Amount of CPU threads"
    )

    cpu_speed = models.DecimalField(
        'CPU speed (MHz)',
        default=0,
        max_digits=10,
        decimal_places=2
    )

    cpu_id = models.CharField(
        'CPU ID',
        max_length=200,
        blank=True,
        help_text="X86 cpuid value which identifies the CPU family/model/stepping and features"
    )

    ram_amount = models.IntegerField(
        'RAM amount (MB)',
        default=0
    )

    efi = models.BooleanField(
        'EFI boot',
        default=False,
        help_text="Installed in EFI (aarch64/x86) mode?"
    )

    nda = models.BooleanField(
        'NDA hardware',
        default=False,
        help_text="This machine is under NDA and has secret (early development HW?) partner information, do not share any data to the outside world"
    )

    ipmi = models.BooleanField(
        'IPMI capability',
        default=False,
        help_text="IPMI service processor (BMC) detected"
    )

    vm_capable = models.BooleanField(
        'VM capable',
        default=False,
        help_text="Do the CPUs support native virtualization (KVM). This field is deprecated"
    )

    vm_max = models.IntegerField(
        'Max. VMs',
        default=6,
        help_text="Maximum amount of virtual hosts allowed to be spawned on this virtual server (ToDo: don't use yet)"
    )

    vm_dedicated_host = models.BooleanField(
        'Dedicated VM host',
        default=False,
        help_text="Dedicated to serve as physical host for virtual machines (users cannot reserve this machine)"
    )

    vm_auto_delete = models.BooleanField(
        'Delete automatically',
        default=False,
        help_text="Release and destroy virtual machine instances, once people have released (do not reserve anymore) them"
    )

    virt_api_int = models.SmallIntegerField(
        'Virtualization API',
        choices=VirtualizationAPI.TYPE_CHOICES,
        blank=True,
        null=True,
        help_text="Only supported API currently is libvirt"
    )

    reserved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    reserved_at = models.DateTimeField(
        blank=True,
        null=True
    )

    reserved_until = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Reservation expires at xx.yy.zzzz (max 90 days)"
    )

    reserved_reason = models.CharField(
        'Reservation reason',
        max_length=512,
        blank=True,
        null=True,
        help_text="Why do you need this machine (bug no, jira feature, what do you test/work on)?"
    )

    platform = models.ForeignKey(
        Platform,
        blank=True,
        null=True,
        limit_choices_to={'is_cartridge': True},
        on_delete=models.SET_NULL
    )

    bios_version = models.CharField(
        max_length=200,
        blank=True,
        help_text="The firmware BIOS is from ... (on x86 as retrieved from dmidecode -s bios-version"
    )

    bios_date = models.DateField(
        editable=False,
        blank=True,
        null=True,
        default=None,
        help_text="The firmware BIOS is from ... (on x86 as retrieved from dmidecode -s bios-version"
    )

    disk_primary_size = models.SmallIntegerField(
        'Disk primary size (GB)',
        null=True,
        blank=True
    )

    disk_type = models.CharField(
        max_length=100,
        blank=True
    )

    lsmod = models.TextField(blank=True)

    last = models.CharField(
        max_length=100,
        blank=True
    )

    hwinfo = models.TextField(blank=True)

    dmidecode = models.TextField(blank=True)

    dmesg = models.TextField(blank=True)

    lsscsi = models.TextField(blank=True)

    lsusb = models.TextField(blank=True)

    lspci = models.TextField(blank=True)

    status_ipv4 = models.SmallIntegerField(
        'Status IPv4',
        choices=StatusIP.CHOICE,
        editable=False,
        default=StatusIP.UNREACHABLE,
        help_text="Does this IPv4 address respond to ping?"
    )

    status_ipv6 = models.SmallIntegerField(
        'Status IPv6',
        choices=StatusIP.CHOICE,
        editable=False,
        default=StatusIP.UNREACHABLE,
        help_text="Does this IPv6 address respond to ping?"
    )

    status_ssh = models.BooleanField(
        'SSH',
        editable=False,
        default=False,
        help_text="Is the ssh port (22) on this host address open?"
    )

    status_login = models.BooleanField(
        'Login',
        editable=False,
        default=False,
        help_text="Can orthos log into this host via ssh key (if not scanned data might be outdated)?"
    )

    administrative = models.BooleanField(
        'Administrative machine',
        editable=True,
        default=False,
        help_text="Administrative machines cannot be reserved"
    )

    check_connectivity = models.SmallIntegerField(
        choices=CONNECTIVITY_CHOICE,
        default=Connectivity.ALL,
        blank=False,
        help_text='Nightly checks whether the machine responds to ping, ssh port is open or whether orthos can log in via ssh key. Can be triggered manually via command\
 line client: `rescan [fqdn] status`'
    )

    collect_system_information = models.BooleanField(
        default=True,
        help_text='Shall the system be scanned every night? This only works if the proper ssh key is in place in authorized_keys and can be triggered manually via command line client: `rescan [fqdn]`'
    )

    dhcp_filename = models.CharField(
        'DHCP filename',
        max_length=64,
        null=True,
        blank=True,
        help_text="Override bootloader binary retrieved from a tftp server (corresponds to the `filename` ISC dhcpd.conf variable)"
    )

    tftp_server = models.ForeignKey(
        'data.Machine',
        related_name='tftp_server_for',
        verbose_name='TFTP server',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        limit_choices_to={'administrative': True},
        help_text="Override tftp server used for network boot (corresponds to the `next_server` ISC dhcpd.conf variable)"
    )

    hypervisor = models.ForeignKey(
        'data.Machine',
        related_name="hypervising",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="The physical host this virtual machine is running on"
    )
    hostname = None

    __ipv4 = None

    __ipv6 = None

    mac_address = None

    # Runtime object created on virt_api_int in init()
    virtualization_api = None

    unknown_mac = models.BooleanField(
        default=False,
        verbose_name="MAC unknwon",
        help_text="Use this to create a BMC before the mac address of the machine is known"
    )

    active = models.BooleanField(
        default=True
    )

    group = models.ForeignKey(
        MachineGroup,
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )

    contact_email = models.EmailField(
        blank=True,
        help_text="Override contact email address to whom is in charge for this machine"
    )

    kernel_options = models.CharField(
        max_length=4096,
        blank=True,
        help_text="Additional kernel command line parameters to pass"
    )

    last_check = models.DateTimeField(
        'Checked at',
        editable=False,
        default='2016-01-01T10:00:00+00:00'
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
    api = RootManager()
    active_machines = RootManager()
    search = SearchManager()
    view = ViewManager()

    def __init__(self, *args, **kwargs):
        """Deep copy object for comparison in `save()`."""
        super(Machine, self).__init__(*args, **kwargs)

        if self.pk is not None:
            self._original = deepcopy(self)
        else:
            self._original = None

        if self.virt_api_int is not None:
            self.virtualization_api = VirtualizationAPI(self.virt_api_int, self)

    def __str__(self):
        return self.fqdn

    def bmc_allowed(self):
        return self.system.allowBMC

    def has_bmc(self):
        return hasattr(self, 'bmc')

    def save(self, *args, **kwargs):
        """
        Save machine object.

        Set FQDN to lower case, check if FQDN is resolvable by DNS and set
        domain and enclosure correctly (create if necessary).
        """
        self.fqdn = self.fqdn.lower()

        if not self.mac_address and not self.unknown_mac:
            raise ValidationError("'{}' You must select 'MAC Unkown' for systems without MAC".format(self))

        if self.mac_address and self.unknown_mac:
            raise ValidationError("'{}' You must not select 'MAC Unkown' for systems with a MAC".format(self))
        if self.unknown_mac and not self.bmc_allowed():
            raise ValidationError("You may only skip the MAC for systems with BMC")
        if self.mac_address:
            validate_mac_address(self.mac_address)

        if not self.system.virtual and self.hypervisor:
            raise ValidationError("Only virtual machines may have hypervisors")
        if hasattr(self, 'bmc') and not self.bmc_allowed():
            raise ValidationError("{} systems cannot use a BMC".format(self.system.name))
        # create & assign network domain and ensure that the FQDN always matches the fqdn_domain
        domain, created = Domain.objects.get_or_create(name=get_domain(self.fqdn))
        if created:
            domain.save()
        self.fqdn_domain = domain

        # create & assign enclosure according to naming convention if no enclosure given
        if not hasattr(self, 'enclosure'):
            name = re.split(r'-(\d|sp)+$', get_hostname(self.fqdn))[0]
            enclosure, created = Enclosure.objects.get_or_create(name=name)
            self.enclosure = enclosure

        super(Machine, self).save(*args, **kwargs)

        # check if DHCP needs to be regenerated
        if self._original is not None:
            try:
                assert self.mac_address == self._original.mac_address
                assert self.fqdn == self._original.fqdn
                assert self.fqdn_domain == self._original.fqdn_domain
                assert self.architecture == self._original.architecture
                assert self.group == self._original.group
                assert self.dhcp_filename == self._original.dhcp_filename
                assert self.kernel_options == self._original.kernel_options
                if self.has_remotepower():
                    assert hasattr(self._original, 'remotepower')
                    assert self.remotepower.fence_name == self._original.remotepower.fence_name
                    assert self.remotepower.options == self._original.remotepower.options
                    if hasattr(self.remotepower, 'remote_power_device'):
                        assert hasattr(self._original.remotepower, 'remote_power_device')
                        assert self.remotepower.remote_power_device == \
                               self._original.remotepower.remote_power_device
                if hasattr(self, 'bmc'):
                    assert hasattr(self._original, 'bmc')
                    assert self.bmc.username == self._original.bmc.username
                    assert self.bmc.password == self._original.bmc.password
                    assert self.bmc.mac == self._original.bmc.mac
                    assert self.bmc.fqdn == self._original.bmc.fqdn
                if self.has_serialconsole():
                    assert hasattr(self._original, 'serialconsole')
                    assert self.serialconsole.baud_rate == self._original.serialconsole.baud_rate
                    assert self.serialconsole.kernel_device_num == \
                        self._original.serialconsole.kernel_device_num
            except AssertionError:
                if ServerConfig.objects.bool_by_key("orthos.cobblersync.full"):
                    from orthos2.data.signals import signal_cobbler_regenerate

                    # regenerate DHCP on all domains (deletion/registration) if domain changed
                    if self.fqdn_domain == self._original.fqdn_domain:
                        domain_id = self.fqdn_domain.pk
                    else:
                        domain_id = None

                    signal_cobbler_regenerate.send(sender=self.__class__, domain_id=domain_id)
                else:
                    from orthos2.data.signals import signal_cobbler_machine_update
                    if self.fqdn_domain == self._original.fqdn_domain:
                        domain_id = self.fqdn_domain.pk
                        machine_id = self.pk
                        signal_cobbler_machine_update.send(
                            sender=self.__class__, domain_id=domain_id, machine_id=machine_id)
                    else:
                        raise NotImplementedError(
                            "Moving machines between domains with quick cobbler synchronization "
                            "is not implemented yet")

    @property
    def ipv4(self):
        if self.__ipv4 is None:
            self.__ipv4 = get_ipv4(self.fqdn)
        return self.__ipv4

    @property
    def ipv6(self):
        if self.__ipv6 is None:
            self.__ipv6 = get_ipv6(self.fqdn)
        return self.__ipv6

    @property
    def status_ping(self):
        return self.status_ipv4 in {Machine.StatusIP.REACHABLE, Machine.StatusIP.CONFIRMED} or\
            self.status_ipv6 in {Machine.StatusIP.REACHABLE, Machine.StatusIP.CONFIRMED}

    def is_reserved(self):
        if self.reserved_by:
            return True
        return False
    is_reserved.boolean = True

    def is_administrative(self):
        return self.administrative
    is_administrative.boolean = True

    def is_cobbler_server(self):
        return self.domain_set.all().exists()
    is_cobbler_server.boolean = True

    def is_virtual_machine(self):
        """
        Is this a virtualized system?

        "return: `True` if machine is a virtual machine (system)
        """
        return self.system.virtual

    def is_vm_managed(self):
        """
        Is this a virtual machine and has a hypervisor and virt API assigned
        through which it is managed?

        :return: `True` if machine has a hypervisor and a virtualization API assgined.
        """
        return self.hypervisor and self.hypervisor.virtualization_api

    def get_cobbler_domains(self):
        if not self.is_cobbler_server():
            return None
        return self.domain_set.all()

    def get_active_distribution(self):
        return self.installations.get(active=True)

    def get_primary_networkinterface(self):
        try:
            interface = self.networkinterfaces.get(primary=True)
        except NetworkInterface.DoesNotExist:
            logger.debug("In 'get_primary_networkinterface': Machine %s has no networkinterfce", self.fqdn )
            return None
        return interface

    def get_virtual_machines(self):
        if not self.is_virtual_machine():
            return self.hypervising.all()
        return None

    def get_kernel_options(self):
        """Return kernel options as dict."""
        kernel_options = {}

        if not self.kernel_options.strip().startswith('+'):
            for kernel_option in self.kernel_options.strip().split():
                option = kernel_option.split('=')
                key = option[0]
                value = option[1] if len(option) == 2 else None
                kernel_options[key] = value

        return kernel_options

    def get_kernel_options_append(self):
        """Return kernel options append as dict."""
        kernel_options = {}

        if self.kernel_options.strip().startswith('+'):
            for kernel_option in self.kernel_options.strip()[1:].split():
                option = kernel_option.split('=')
                key = option[0]
                value = option[1] if len(option) == 2 else None
                kernel_options[key] = value

        return kernel_options

    def get_s390_hostname(self, use_uppercase=False):
        if self.system.name == 'zVM':
            return get_s390_hostname(self.hostname, use_uppercase=use_uppercase)
        return None

    def has_remotepower(self):
        """Check for available remote power."""
        return hasattr(self, 'remotepower')

    def has_serialconsole(self):
        """Check for available serial console."""
        return hasattr(self, 'serialconsole')

    def is_reserved_infinite(self):
        """Return true if machine is reserved infinite `datetime.date(9999, 12, 31)`."""
        if self.reserved_by and self.reserved_until.date() == datetime.date.max:
            return True
        return False

    def has_setup_capability(self):
        """
        Return true if a machines network domain supports the setup capability for the respective
        machine group (if the machine belongs to one) or architecture.
        """
        return self.architecture in self.fqdn_domain.supported_architectures.all()

    @check_permission
    def reserve(self, reason, until, user=None, reserve_for_user=None):
        """Reserve machine."""
        from orthos2.taskmanager import tasks
        from orthos2.taskmanager.models import TaskManager

        from .reservationhistory import ReservationHistory

        if not reserve_for_user:
            reserve_for_user = user

        extension = True

        if not reason:
            raise ReserveException("Please provide a reservation reason.")

        if until == datetime.date.max and not user.is_superuser:
            raise ReserveException("Infinite reservation is not allowed.")

        # add to history if a superuser takes over the reservation
        if self.reserved_by and (self.reserved_by not in {user, reserve_for_user}):
            reservationhistory = ReservationHistory(
                machine=self,
                reserved_by=self.reserved_by,
                reserved_at=self.reserved_at,
                reserved_until=timezone.now(),
                reserved_reason='{} (taken away by {})'.format(self.reserved_reason, user)
            )
            reservationhistory.save()
            self.reserved_at = None

        self.reserved_by = reserve_for_user
        self.reserved_reason = reason
        if not self.reserved_at:
            self.reserved_at = timezone.now()
            extension = False

        # Infinte reservation:
        # --------------------
        # Use `datetime.date.max` for the date and `datetime.time.min` for the time.
        # The minimum time (0, 0) must be set so that the correct time zone calculation does not
        # exceed the maximum DateTime limit (CET (UTC+1) of 9999-12-31, 23:59 (UTC) would result
        # in `OverflowError: date value out of range`).

        # Normal reservation (not infinite):
        # ----------------------------------
        # Combine the `datetime.date` object with `datetime.time.max` (23, 59) and make the
        # new `datetime.datetime` object time zone aware using the default time zone (see
        # `TIME_ZONE` in the django settings).
        if until == datetime.date.max:
            until = timezone.datetime.combine(datetime.date.max, timezone.datetime.min.time())
            until = timezone.make_aware(until, timezone.utc)
        else:
            until = timezone.datetime.combine(until, timezone.datetime.max.time())
            until = timezone.make_aware(until, timezone.get_default_timezone())

        self.reserved_until = until
        self.save()

        self.update_motd()

        if not extension:
            task = tasks.SendReservationInformation(reserve_for_user.id, self.fqdn)
            TaskManager.add(task)

    @check_permission
    def release(self, user=None):
        """Release machine."""
        from .reservationhistory import ReservationHistory

        if not self.is_reserved():
            raise ReleaseException("Machine is not reserved.")

        if self.administrative:
            raise Exception("Administrative machines must not be released, remove admin flag first")

        if self.is_vm_managed() and self.hypervisor.vm_auto_delete:
            self.delete()
            return

        reservationhistory = ReservationHistory(
            machine=self,
            reserved_by=self.reserved_by,
            reserved_at=self.reserved_at,
            reserved_until=timezone.now(),
            reserved_reason=self.reserved_reason
        )

        self.reserved_by = None
        self.reserved_reason = None
        self.reserved_at = None
        self.reserved_until = None

        self.save()
        reservationhistory.save()

        if self.has_setup_capability():
            self.setup()
        else:
            self.update_motd()

    @check_permission
    def powercycle(self, action, user=None):
        """Act as proxy for all power cycle actions."""
        from .remotepower import RemotePower

        if (action is None) or (action not in RemotePower.Action.as_list):
            raise Exception("Power cycling failed: unknown action ('{}')!".format(action))

        if not self.has_remotepower():
            raise Exception("No remotepower available!")

        if action == RemotePower.Action.STATUS:
            return self.get_power_status()

        elif action == RemotePower.Action.ON:
            return self.power_on()

        elif action == RemotePower.Action.OFF:
            return self.power_off()

        elif action == RemotePower.Action.REBOOT:
            return self.reboot()

        elif action == RemotePower.Action.OFF_SSH:
            return self.power_off_ssh()

        elif action == RemotePower.Action.OFF_REMOTEPOWER:
            return self.power_off_remotepower()

        elif action == RemotePower.Action.REBOOT_SSH:
            return self.reboot_ssh()

        elif action == RemotePower.Action.REBOOT_REMOTEPOWER:
            if self.has_remotepower():
                return self.reboot_remotepower()

        return False

    @check_permission
    def ssh_shutdown(self, user=None, reboot=False):
        """Power off/reboot the machine using SSH."""
        from orthos2.utils.ssh import SSH

        if reboot:
            option = '--reboot'
        else:
            option = '--poweroff'

        machine = SSH(self.fqdn)
        machine.connect()
        command = 'shutdown {} now'.format(option)
        stdout, stderr, exitstatus = machine.execute(command, retry=False)
        machine.close()

        if exitstatus != 0:
            return False

        return True

    @check_permission
    def setup(self, setup_label=None, user=None):
        """Setup machine (re-install distribution)."""
        from orthos2.taskmanager import tasks
        from orthos2.taskmanager.models import TaskManager

        if self.has_setup_capability():
            task = tasks.SetupMachine(self.fqdn, setup_label)
            TaskManager.add(task)
            return True

        return False

    @check_permission
    def power_on(self, user=None):
        """Power on the machine."""
        self.remotepower.power_on()
        return True

    @check_permission
    def power_off(self, user=None):
        """
        Power off the machine.

        Try power off via SSH first. If SSH didn't succeed, trigger power off via remote power if
        available.
        """
        from orthos2.utils.ssh import SSH

        result = False

        try:
            result = self.ssh_shutdown()
        except SSH.Exception:
            pass

        if result is True:
            return True
        else:
            if self.has_remotepower():
                return self.power_off_remotepower(user=user)

    @check_permission
    def power_off_ssh(self, user=None):
        """Power off the machine using SSH. Wrapper for `ssh_shutdown()`."""
        return self.ssh_shutdown()

    @check_permission
    def power_off_remotepower(self, user=None):
        """Power off the machine via remote power."""
        self.remotepower.power_off()
        return True

    @check_permission
    def reboot(self, user=None):
        """
        Power off the machine.

        Try power off via SSH first. If SSH didn't succeed, trigger power off via remote power if
        available.
        """
        from orthos2.utils.ssh import SSH

        result = False

        try:
            result = self.ssh_shutdown(reboot=True)
        except SSH.Exception:
            pass

        if result is True:
            return True
        else:
            if self.has_remotepower():
                return self.reboot_remotepower(user=user)

    @check_permission
    def reboot_ssh(self, user=None):
        """Reboot the machine using SSH. Wrapper for `ssh_shutdown(reboot=True)`."""
        return self.ssh_shutdown(reboot=True)

    @check_permission
    def reboot_remotepower(self, user=None):
        """Reboot the machine via remote power."""
        if self.has_remotepower():
            self.remotepower.reboot()
        return True

    def get_power_status(self, to_str=True):
        """Return the current power status."""
        from .remotepower import RemotePower

        if not self.has_remotepower():
            return RemotePower.Status.UNKNOWN

        status = self.remotepower.get_status()
        if to_str:
            return RemotePower.Status.to_str(status)
        return status

    def scan(self, action='all', user=None):
        """Start scanning/checking the machine by creating a task."""
        from orthos2.taskmanager import tasks
        from orthos2.taskmanager.tasks.ansible import Ansible
        from orthos2.taskmanager.models import TaskManager

        if action.lower() not in tasks.MachineCheck.Scan.Action.as_list:
            raise Exception("Unknown scan option '{}'!".format(action))

        task = tasks.MachineCheck(self.fqdn, tasks.MachineCheck.Scan.to_int(action))
        TaskManager.add(task)

        #ToDo: Better wait until individual machine scans finished
        task = Ansible([self.fqdn])
        TaskManager.add(task)

    @check_permission
    def update_motd(self, user=None):
        """Call respective signal."""
        from orthos2.data.signals import signal_motd_regenerate

        signal_motd_regenerate.send(sender=self.__class__, fqdn=self.fqdn)

    @check_permission
    def regenerate_serialconsole_record(self, user=None):
        """Call respective signal."""
        from orthos2.data.signals import signal_serialconsole_regenerate

        if self.has_serialconsole():
            signal_serialconsole_regenerate.send(
                sender=self.__class__,
                cscreen_server_fqdn=self.fqdn_domain.cscreen_server.fqdn
            )

    @check_permission
    def regenerate_dhcp_record(self, user=None):
        """Call respective signal."""
        from orthos2.data.signals import signal_cobbler_regenerate

        signal_cobbler_regenerate.send(sender=self.__class__, domain_id=self.fqdn_domain.pk)

    def get_support_contact(self):
        """
        Return email address for responsible support contact (default: SUPPORT_CONTACT).

        Machine > [Group >] Architecture > SUPPORT_CONTACT
        """
        if self.contact_email:
            return self.contact_email

        if self.group:
            contact = self.group.get_support_contact()
            if contact:
                return contact

        admin = DomainAdmin(domain = self.fqdn_domain, arch = self.architecture)
        if admin and admin.contact_email:
            logger.warning("Email admin: %s", admin.contact_email)
            return admin.contact_email

        return settings.SUPPORT_CONTACT

    def serialize(self, output_format):
        """
        Serialize machine with its relations.

        Valid output formats are JSON and Yaml.
        """
        output_format = output_format.lower()

        if not Serializer.Format.is_valid(output_format):
            logger.warning("Unknown serialize format! Continues with JSON...")
            output_format = Serializer.Format.JSON

        if output_format == Serializer.Format.YAML:
            try:
                import yaml
            except ImportError:
                logger.warning("YAML module not available! Continues with JSON...")
                output_format = Serializer.Format.JSON

        querysets = [
            [self],
            self.networkinterfaces.all(),
            [self.remotepower] if self.has_remotepower() else None,
            [self.serialconsole] if self.has_serialconsole() else None,
            self.annotations.all(),
            self.reservationhistory_set.all(),
        ]

        serializer = serializers.get_serializer(output_format)()
        chunks = []

        for i, queryset in enumerate(querysets):

            if queryset is None:
                continue

            chunks.append(serializer.serialize(
                queryset,
                indent=4,
                use_natural_foreign_keys=True,
                use_natural_primary_keys=True
            ))

        data = '\n'.join(chunks)

        return (data, output_format)
