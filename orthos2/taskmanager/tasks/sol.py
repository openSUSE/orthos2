import ipaddress
import logging
import re
import shlex

from orthos2.data.models import Machine, ServerConfig
from orthos2.taskmanager.models import Task
from orthos2.utils.ssh import SSH

logger = logging.getLogger("tasks")


class DeactivateSerialOverLan(Task):
    """Deactivate SOL for a machine from its serial console server."""

    def __init__(self, machine_id: int) -> None:
        self.machine_id = machine_id

    def execute(self) -> None:
        timeout_seconds = 30.0

        try:
            machine = Machine.objects.get(pk=self.machine_id)
        except Machine.DoesNotExist:
            logger.error("Machine does not exist: id=%s", self.machine_id)
            return

        if (
            not machine.has_serialconsole()
            or machine.serialconsole.stype.name != "IPMI"
        ):
            logger.error(
                "SOL deactivate skipped for non-IPMI machine: %s", machine.fqdn
            )
            return

        if not machine.has_bmc():
            logger.error(
                "SOL deactivate skipped because machine has no BMC: %s", machine.fqdn
            )
            return

        cscreen_server = machine.fqdn_domain.cscreen_server
        if not cscreen_server:
            logger.error(
                "SOL deactivate skipped because no cscreen server is configured: %s",
                machine.fqdn,
            )
            return

        host = (machine.bmc.fqdn or "").strip()
        username = (
            machine.bmc.username
            or ServerConfig.get_server_config_manager().by_key(
                "serialconsole.ipmi.username", ""
            )
            or ""
        ).strip()
        password = (
            machine.bmc.password
            or ServerConfig.get_server_config_manager().by_key(
                "serialconsole.ipmi.password", ""
            )
            or ""
        )

        if not host:
            logger.error(
                "SOL deactivate skipped because BMC host is empty: %s", machine.fqdn
            )
            return

        if not username:
            logger.error(
                "SOL deactivate skipped because IPMI username is empty: %s",
                machine.fqdn,
            )
            return

        if any(char in host for char in ("\x00", "\r", "\n")):
            logger.error(
                "SOL deactivate skipped because BMC host is invalid: %s", machine.fqdn
            )
            return

        host_is_hostname = re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.-]*", host) is not None
        host_is_ip = False
        try:
            ipaddress.ip_address(host)
            host_is_ip = True
        except ValueError:
            pass

        if not (host_is_hostname or host_is_ip):
            logger.error(
                "SOL deactivate skipped because BMC host is invalid: %s", machine.fqdn
            )
            return

        if re.fullmatch(r"[A-Za-z0-9_.@-]+", username) is None:
            logger.error(
                "SOL deactivate skipped because IPMI username is invalid: %s",
                machine.fqdn,
            )
            return

        if "\x00" in password:
            logger.error(
                "SOL deactivate skipped because IPMI password contains null byte: %s",
                machine.fqdn,
            )
            return

        command = "/usr/bin/ipmitool -I lanplus -H {} -U {} -E sol deactivate".format(
            shlex.quote(host),
            shlex.quote(username),
        )

        conn = None
        try:
            conn = SSH(cscreen_server.fqdn)
            conn.connect(user="_cscreen")
            _stdout, stderr, exitstatus = conn.execute(
                command,
                retry=False,
                timeout=timeout_seconds,
                environment={"IPMI_PASSWORD": password},
            )
            if exitstatus != 0:
                logger.error(
                    "SOL deactivate failed for %s via %s: %s",
                    machine.fqdn,
                    cscreen_server.fqdn,
                    "".join(stderr).strip(),
                )
                return
            logger.info(
                "SOL deactivate finished for %s via %s",
                machine.fqdn,
                cscreen_server.fqdn,
            )
        except SSH.Exception as exception:
            logger.exception(exception)
        finally:
            if conn:
                conn.close()
