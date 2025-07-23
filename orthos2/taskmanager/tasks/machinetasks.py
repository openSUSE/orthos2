import logging
from typing import Callable, Optional, Tuple

from django.utils import timezone

from orthos2.data.models import Machine, ServerConfig
from orthos2.taskmanager.models import Task
from orthos2.utils.machinechecks import (
    get_installations,
    get_status_ip,
    login_test,
    nmap_check,
    ping_check_ipv4,
    ping_check_ipv6,
)
from orthos2.utils.misc import sync, wrap80
from orthos2.utils.ssh import SSH

logger = logging.getLogger("tasks")


class MachineCheck(Task):
    """
    Checks a machine.
    """

    class Scan:
        class Action:
            STATUS = "status"
            NETWORKINTERFACES = "networkinterfaces"
            INSTALLATIONS = "installations"
            ALL = "all"

            as_list = [STATUS, NETWORKINTERFACES, INSTALLATIONS, ALL]

        STATUS = 0
        NETWORKINTERFACES = 1
        INSTALLATIONS = 2
        ALL = 99

        as_list = [STATUS, NETWORKINTERFACES, INSTALLATIONS, ALL]

        @classmethod
        def to_str(cls, index: int) -> str:
            """
            Returns scan option as string by index.
            """
            for type_tuple in MachineCheck.SCAN_CHOICES:
                if int(index) == type_tuple[0]:
                    return type_tuple[1]
            raise Exception("Scan option '{}' doesn't exist!".format(index))

        @classmethod
        def to_int(cls, name: str) -> int:
            """
            Returns scan option as integer if name matches.
            """
            for type_tuple in MachineCheck.SCAN_CHOICES:
                if name.lower() == type_tuple[1].lower():
                    return type_tuple[0]
            raise Exception("Unknown scan option '{}'!".format(name))

    SCAN_CHOICES = (
        (Scan.STATUS, Scan.Action.STATUS),
        (Scan.NETWORKINTERFACES, Scan.Action.NETWORKINTERFACES),
        (Scan.INSTALLATIONS, Scan.Action.INSTALLATIONS),
        (Scan.ALL, Scan.Action.ALL),
    )

    def __init__(self, fqdn: str, scan: int) -> None:
        self.fqdn = fqdn
        self.scan = scan
        self.machine = None
        self.online = None

    def _get_methods(self) -> Tuple[Callable[[], None], ...]:
        """
        Returns all check-methods for the respective scans.
        """
        methods = {
            self.Scan.STATUS: (self.status,),
            self.Scan.NETWORKINTERFACES: (self.status_ip,),
            self.Scan.INSTALLATIONS: (self.installations,),
            self.Scan.ALL: (
                self.status,
                self.status_ip,
                self.installations,
            ),
        }

        return methods[self.scan]

    def set_scan(self, scan: int) -> None:
        """
        Set the scan scope.
        """
        self.scan = scan

    def status(self) -> None:
        """
        Checks ping, SSH and login status.
        """
        if self.machine is None:
            raise ValueError("Machine not set!")

        self.machine.status_ipv4 = Machine.StatusIP.UNREACHABLE
        self.machine.status_ipv6 = Machine.StatusIP.UNREACHABLE
        self.machine.status_ssh = False
        self.machine.status_login = False

        if self.machine.check_connectivity > Machine.Connectivity.NONE:
            if ping_check_ipv4(self.fqdn, timeout=1):
                self.machine.status_ipv4 = Machine.StatusIP.REACHABLE
            if ping_check_ipv6(self.fqdn, timeout=1):
                self.machine.status_ipv6 = Machine.StatusIP.REACHABLE

            if (
                self.machine.status_ping
                and self.machine.check_connectivity > Machine.Connectivity.PING
            ):
                self.machine.status_ssh = nmap_check(self.fqdn)

                if (
                    self.machine.status_ssh
                    and self.machine.check_connectivity > Machine.Connectivity.SSH
                ):
                    self.machine.status_login = login_test(self.fqdn)
        self.online = bool(self.machine.status_login)
        self.machine.save()

    def status_ip(self) -> None:
        """
        Collect IPv4/IPv6 status.
        """
        if self.machine is None:
            raise ValueError("Machine not set!")

        if not self.machine.collect_system_information:
            logger.debug("Status IP: collecting system information disabled... skip")
            return

        if self.online is False:
            return

        machine_ = get_status_ip(self.fqdn)
        if isinstance(machine_, bool) or not machine_:
            return

        if machine_:
            sync(self.machine, machine_)

    def installations(self) -> None:
        """
        Collect all installations/distributions.
        """
        if not self.machine.collect_system_information:  # type: ignore
            logger.debug(
                "Installations: collecting system information disabled... skip"
            )
            return

        if self.online is False:
            return

        installations_ = get_installations(self.fqdn)

        if isinstance(installations_, bool) or not installations_:
            return

        logger.debug("Drop installations for '%s'...", self.fqdn)
        self.machine.installations.all().delete()  # type: ignore

        for installation in installations_:
            installation.save()

    def execute(self) -> None:
        """
        Executes the task.
        """
        try:
            self.machine = Machine.objects.get(fqdn=self.fqdn)  # type: ignore
        except Machine.DoesNotExist:
            logger.error("Machine does not exist: fqdn=%s", self.fqdn)
            return

        for func in self._get_methods():
            func()

        self.machine.last_check = timezone.now()  # type: ignore
        self.machine.save()  # type: ignore


class RegenerateMOTD(Task):
    """
    Regenerates the MOTD of a machine.
    """

    def __init__(self, fqdn: str) -> None:
        self.fqdn = fqdn

    def execute(self) -> Optional[bool]:  # type: ignore
        """
        Executes the task.
        """
        if not ServerConfig.get_server_config_manager().bool_by_key(
            "orthos.debug.motd.write"
        ):
            logger.warning("Disabled: set 'orthos.debug.motd.write' to 'true'")
            return None

        BEGIN = "-" * 69 + " Orthos{ --"
        LINE = "-" * 80
        END = "-" * 69 + " Orthos} --"

        try:
            machine = Machine.objects.get(fqdn=self.fqdn)
        except Machine.DoesNotExist:
            logger.error("Machine does not exist: fqdn=%s", self.fqdn)
            return None

        conn = None
        try:
            conn = SSH(machine.fqdn)
            conn.connect()
            motd = conn.get_file("/etc/motd.orthos", "w")
            print(BEGIN, file=motd)
            print(
                "Machine of the ARCH team. Contact <{}> for problems.".format(
                    machine.get_support_contact()
                ),
                file=motd,
            )
            if machine.comment:
                print("INFO: " + machine.comment, file=motd)
            if machine.administrative:
                print(
                    "This machine is an administrative machine. DON'T TOUCH!", file=motd
                )
            if machine.reserved_by:
                print(LINE, file=motd)
                if machine.is_reserved_infinite():
                    print(
                        "This machine is RESERVED by {} (infinite).".format(
                            machine.reserved_by
                        ),
                        file=motd,
                    )
                else:
                    print(
                        "This machine is RESERVED by {} until {}.".format(
                            machine.reserved_by, machine.reserved_until
                        ),
                        file=motd,
                    )
                print("", file=motd)
                print(wrap80(machine.reserved_reason), file=motd)  # type: ignore
            print(END, file=motd)
            motd.close()
            script_result = conn.execute_script_remote("machine_sync_motd.sh")
            if script_result is None:
                raise RuntimeError(
                    "Script result for machine_sync_motd.sh wasn't available"
                )
            _stdout, stderr, exitstatus = script_result

            if exitstatus != 0:
                logger.exception("(%s) %s", machine.fqdn, stderr)
                raise Exception(stderr)

        except SSH.Exception as e:
            logger.error("(%s) %s", machine.fqdn, e)
            return False
        except IOError as e:
            logger.error("(%s) %s", machine.fqdn, e)
            return False
        finally:
            if conn:
                conn.close()
