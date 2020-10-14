import logging

from data.models import Machine, NetworkInterface, ServerConfig
from django.utils import timezone
from taskmanager.models import Task
from utils.machinechecks import (abuild_test, get_hardware_information,
                                 get_installations, get_networkinterfaces,
                                 get_pci_devices, get_status_ip, login_test,
                                 nmap_check, ping_check_ipv4, ping_check_ipv6)
from utils.misc import sync, wrap80
from utils.ssh import SSH

logger = logging.getLogger('tasks')


class MachineCheck(Task):
    """
    Checks a machine.
    """

    class Scan:

        class Action:
            STATUS = 'status'
            MISC = 'misc'
            NETWORKINTERFACES = 'networkinterfaces'
            INSTALLATIONS = 'installations'
            ALL = 'all'

            as_list = [STATUS, MISC, NETWORKINTERFACES, INSTALLATIONS, ALL]

        STATUS = 0
        MISC = 1
        NETWORKINTERFACES = 2
        INSTALLATIONS = 3
        ALL = 99

        as_list = [STATUS, MISC, NETWORKINTERFACES, INSTALLATIONS, ALL]

        @classmethod
        def to_str(cls, index):
            """
            Returns scan option as string by index.
            """
            for type_tuple in MachineCheck.SCAN_CHOICES:
                if int(index) == type_tuple[0]:
                    return type_tuple[1]
            raise Exception("Scan option '{}' doesn't exist!".format(index))

        @classmethod
        def to_int(cls, name):
            """
            Returns scan option as integer if name matches.
            """
            for type_tuple in MachineCheck.SCAN_CHOICES:
                if name.lower() == type_tuple[1].lower():
                    return type_tuple[0]
            raise Exception("Unknown scan option '{}'!".format(name))

    SCAN_CHOICES = (
        (Scan.STATUS, Scan.Action.STATUS),
        (Scan.MISC, Scan.Action.MISC),
        (Scan.NETWORKINTERFACES, Scan.Action.NETWORKINTERFACES),
        (Scan.INSTALLATIONS, Scan.Action.INSTALLATIONS),
        (Scan.ALL, Scan.Action.ALL),
    )

    def __init__(self, fqdn, scan):
        self.fqdn = fqdn
        self.scan = scan
        self.machine = None
        self.online = None

    def _get_methods(self):
        """
        Returns all check-methods for the respective scans.
        """
        methods = {
            self.Scan.STATUS: (
                self.status,
            ),
            self.Scan.MISC: (
                self.miscellaneous,
            ),
            self.Scan.NETWORKINTERFACES: (
                self.network,
                self.status_ip,
            ),
            self.Scan.INSTALLATIONS: (
                self.installations,
            ),
            self.Scan.ALL: (
                self.status,
                self.miscellaneous,
                self.network,
                self.status_ip,
                self.installations,
                self.pci_devices,
            )
        }

        return methods[self.scan]

    def set_scan(self, scan):
        """
        Set the scan scope.
        """
        self.scan = scan

    def status(self):
        """
        Checks ping, SSH, login and ABuild status.
        """
        self.machine.status_ipv4 = Machine.StatusIP.UNREACHABLE
        self.machine.status_ipv6 = Machine.StatusIP.UNREACHABLE
        self.machine.status_ssh = False
        self.machine.status_login = False
        self.machine.status_abuild = False

        if self.machine.check_connectivity > Machine.Connectivity.NONE:
            if ping_check_ipv4(self.fqdn, timeout=1):
                self.machine.status_ipv4 = Machine.StatusIP.REACHABLE
            if ping_check_ipv6(self.fqdn, timeout=1):
                self.machine.status_ipv6 = Machine.StatusIP.REACHABLE

            if self.machine.status_ping and\
                    self.machine.check_connectivity > Machine.Connectivity.PING:
                self.machine.status_ssh = nmap_check(self.fqdn)

                if self.machine.status_ssh and\
                        self.machine.check_connectivity > Machine.Connectivity.SSH:
                    self.machine.status_login = login_test(self.fqdn)

                    if self.machine.check_abuild and\
                            self.machine.check_connectivity == Machine.Connectivity.ALL:
                        self.machine.status_abuild = abuild_test(self.fqdn)

        self.online = bool(self.machine.status_login)

        self.machine.save()

    def miscellaneous(self):
        """
        Collect miscellaneous data about CPU, RAM, EFI, VM host capability, etc.
        """
        if not self.machine.collect_system_information:
            logger.debug("Miscellaneous: collecting system information disabled... skip")
            return

        if self.online is False:
            return

        machine_ = get_hardware_information(self.fqdn)

        if machine_:
            sync(self.machine, machine_)

    def network(self):
        """
        Collect information about network interfaces.
        """
        if not self.machine.collect_system_information:
            logger.debug("Network interfaces: collecting system information disabled... skip")
            return

        if self.online is False:
            return

        networkinterfaces_ = get_networkinterfaces(self.fqdn)

        if not networkinterfaces_:
            return None

        for interface in networkinterfaces_:
            networkinterface, created = NetworkInterface.objects.get_or_create(
                machine=self.machine,
                mac_address=interface.mac_address
            )
            networkinterface.ethernet_type = interface.ethernet_type
            networkinterface.driver_module = interface.driver_module
            networkinterface.name = interface.name

            networkinterface.save()

        for networkinterface in self.machine.networkinterfaces.all():
            if networkinterface.mac_address not in\
                    {item.mac_address for item in networkinterfaces_}:

                if not networkinterface.primary:
                    networkinterface.delete()

    def status_ip(self):
        """
        Collect IPv4/IPv6 status.
        """
        if not self.machine.collect_system_information:
            logger.debug("Status IP: collecting system information disabled... skip")
            return

        if self.online is False:
            return

        machine_ = get_status_ip(self.fqdn)

        if machine_:
            sync(self.machine, machine_)

    def installations(self):
        """
        Collect all installations/distributions.
        """
        if not self.machine.collect_system_information:
            logger.debug("Installations: collecting system information disabled... skip")
            return

        if self.online is False:
            return

        installations_ = get_installations(self.fqdn)

        if not installations_:
            return

        logger.debug("Drop installations for '{}'...".format(self.fqdn))
        self.machine.installations.all().delete()

        for installation in installations_:
            installation.save()

    def pci_devices(self):
        """
        Collect all PCI devices.
        """
        if not self.machine.collect_system_information:
            logger.debug("PCI devices: collecting system information disabled... skip")
            return

        if self.online is False:
            return

        pci_devices_ = get_pci_devices(self.fqdn)

        if not pci_devices_:
            return

        logger.debug("Drop PCI devices for '{}'...".format(self.fqdn))
        self.machine.pcidevice_set.all().delete()

        for pci_device in pci_devices_:
            pci_device.save()

    def execute(self):
        """
        Executes the task.
        """
        try:
            self.machine = Machine.objects.get(fqdn=self.fqdn)
        except Machine.DoesNotExist:
            logger.error("Machine does not exist: fqdn={}".format(self.fqdn))
            return

        for func in self._get_methods():
            func()

        self.machine.last_check = timezone.now()
        self.machine.save()


class RegenerateMOTD(Task):
    """
    Regenerates the MOTD of a machine.
    """

    def __init__(self, fqdn):
        self.fqdn = fqdn

    def execute(self):
        """
        Executes the task.
        """
        if not ServerConfig.objects.bool_by_key('orthos.debug.motd.write'):
            logger.warning("Disabled: set 'orthos.debug.motd.write' to 'true'")
            return

        BEGIN = '-' * 69 + ' Orthos{ --'
        LINE = '-' * 80
        END = '-' * 69 + ' Orthos} --'

        try:
            machine = Machine.objects.get(fqdn=self.fqdn)
        except Machine.DoesNotExist:
            logger.error("Machine does not exist: fqdn={}".format(self.fqdn))
            return

        conn = None
        try:
            conn = SSH(machine.fqdn)
            conn.connect()
            motd = conn.get_file('/etc/motd.orthos', 'w')
            print(BEGIN, file=motd)
            print(
                "Machine of the ARCH team. Contact <{}> for problems.".format(
                    machine.get_support_contact()
                ),
                file=motd
            )
            if machine.comment:
                print("INFO: " + machine.comment, file=motd)
            if machine.administrative:
                print("This machine is an administrative machine. DON\'T TOUCH!", file=motd)
            if machine.reserved_by:
                print(LINE, file=motd)
                if machine.reserved_until == timezone.ZERO:
                    print("This machine is RESERVED by {}.".format(machine.reserved_by), file=motd)
                else:
                    print(
                        "This machine is RESERVED by {} until {}.".format(
                            machine.reserved_by,
                            machine.reserved_until
                        ), file=motd
                    )
                print('', file=motd)
                print(wrap80(machine.reserved_reason), file=motd)
            print(END, file=motd)
            motd.close()
            stdout, stderr, exitstatus = conn.execute_script_remote('machine_sync_motd.sh')

            if exitstatus != 0:
                logger.exception("({}) {}".format(machine.fqdn, stderr))
                raise Exception(stderr)

        except SSH.Exception as e:
            logger.error("({}) {}".format(machine.fqdn, e))
            return False
        except IOError as e:
            logger.error("({}) {}".format(machine.fqdn, e))
            return False
        finally:
            if conn:
                conn.close()
