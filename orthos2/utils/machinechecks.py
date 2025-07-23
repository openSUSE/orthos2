import logging
import re
import socket
import threading
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from orthos2.data.models import Installation, Machine
from orthos2.utils.misc import execute
from orthos2.utils.remote import ssh_execute
from orthos2.utils.ssh import SSH

if TYPE_CHECKING:
    from orthos2.data.models.components.pci import PCIDevice

ARPHRD_IEEE80211 = 801

logger = logging.getLogger("utils")


def ping_check(fqdn: str, timeout: Optional[int] = None, ip_version: int = 4) -> bool:
    """Check if the server pings."""
    command = "/usr/bin/ping -4"
    if ip_version == 6:
        command = "/usr/bin/ping6"

    if timeout is None:
        _stdout, _stderr, returncode = execute("{} -c1 -q {}".format(command, fqdn))
    else:
        _stdout, _stderr, returncode = execute(
            "{} -W{} -c1 -q {}".format(command, timeout, fqdn)
        )

    return returncode == 0


def ping_check_ipv4(fqdn: str, timeout: int) -> bool:
    return ping_check(fqdn, timeout, ip_version=4)


def ping_check_ipv6(fqdn: str, timeout: int) -> bool:
    return ping_check(fqdn, timeout, ip_version=6)


def nmap_check(fqdn: str) -> bool:
    """Check if the SSH port is reachable without connectiong."""
    SSH_PORT = 22
    if not ping_check(fqdn):
        return False

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    try:
        s.connect((fqdn, SSH_PORT))
    except socket.error:
        return False
    finally:
        s.close()

    return True


def login_test(fqdn: str) -> bool:
    """Check if it's possible to login via SSH."""
    _stdout, _stderr, err = ssh_execute("exit", fqdn, log_error=False)
    if err:
        logger.warning("SSH login failed for %s", fqdn)
        return False
    return True


def get_status_ip(fqdn: str) -> Optional[Union[bool, Machine]]:
    """Retrieve information of the systems IPv4/IPv6 status."""
    try:
        machine = Machine.objects.get(fqdn=fqdn)
    except Machine.DoesNotExist:
        logger.warning("Machine '%s' does not exist", fqdn)
        return False

    machine_ = Machine()

    logger.debug("Check IPv4/IPv6 status...")

    stdout, _stderr, err = ssh_execute("/sbin/ip a", fqdn)
    if err:
        logger.warning("Machine '%s' could not check IP", fqdn)
        return None
    _file = open("/tmp/orthos_t", "w")
    print(stdout, file=_file)
    _file.close()
    devices: Dict[str, Optional[Union[List[str], str]]] = {}
    current_device = None
    addresses: Dict[str, List[Any]] = {"inet": [], "inet6": []}

    for line in stdout:
        match = re.match(r"^\d+:\s+([a-zA-Z0-9]+):\s+<.*>\s(.*)", line)
        if match:
            current_device = match.group(1)
            devices[current_device] = {  # type: ignore
                "mac_address": None,
                "inet": None,
                "inet6": None,
                "flags": None,
            }
            devices[current_device]["flags"] = match.group(2).split()  # type: ignore
            continue

        line = line.lstrip()

        match = re.match(r"inet ([0-9.]{7,15})\/.*scope", line)
        if match:
            if devices[current_device]["inet"] is None:  # type: ignore
                devices[current_device]["inet"] = []  # type: ignore
            devices[current_device]["inet"].append(match.group(1))  # type: ignore
            continue

        match = re.match(r"inet6 ([a-f0-9:]*)\/[0-9]+ scope", line)
        if match:
            if devices[current_device]["inet6"] is None:  # type: ignore
                devices[current_device]["inet6"] = []  # type: ignore
            devices[current_device]["inet6"].append(match.group(1))  # type: ignore
            continue

        match = re.match("link/ether ([a-f0-9:]{17}) brd", line)
        if match:
            devices[current_device]["mac_address"] = match.group(1).upper()  # type: ignore

    for _device, values in devices.items():
        if values["mac_address"] is None:  # type: ignore
            continue

        # ignore device if hooking up another
        if any(device in values["flags"] for device in devices.keys()):  # type: ignore
            continue

        if values["mac_address"] == machine.mac_address:  # type: ignore
            if values["inet"] is None:  # type: ignore
                machine_.status_ipv4 = Machine.StatusIP.AF_DISABLED
            elif machine.ip_address_v4 not in values["inet"]:  # type: ignore
                machine_.status_ipv4 = Machine.StatusIP.NO_ADDRESS
                if [
                    ipv4
                    for ipv4 in values["inet"]  # type: ignore
                    if not ipv4.startswith("127.0.0.1")  # type: ignore
                ]:
                    machine_.status_ipv4 = Machine.StatusIP.ADDRESS_MISMATCH
            elif machine.ip_address_v4 in values["inet"]:  # type: ignore
                machine_.status_ipv4 = Machine.StatusIP.CONFIRMED
            else:
                machine_.status_ipv4 = Machine.StatusIP.MISSING  # type: ignore

            if values["inet6"] is None:  # type: ignore
                machine_.status_ipv6 = Machine.StatusIP.AF_DISABLED
            elif machine.ip_address_v6 not in values["inet6"]:  # type: ignore
                machine_.status_ipv6 = Machine.StatusIP.NO_ADDRESS
                ipv6_ips: List[str] = [
                    ipv6
                    for ipv6 in values["inet6"]  # type: ignore
                    if not ipv6.startswith("fe80::")  # type: ignore
                ]
                if ipv6_ips:
                    machine_.status_ipv6 = Machine.StatusIP.ADDRESS_MISMATCH
            elif machine.ip_address_v6 in values["inet6"]:  # type: ignore
                machine_.status_ipv6 = Machine.StatusIP.CONFIRMED

        addresses["inet"].append(values["inet"])  # type: ignore
        addresses["inet6"].append(values["inet6"])  # type: ignore

    if machine_.status_ipv4 == Machine.StatusIP.NO_ADDRESS:
        if machine.ip_address_v4 in addresses["inet"]:
            machine_.status_ipv4 = Machine.StatusIP.MAC_MISMATCH

    if machine_.status_ipv6 == Machine.StatusIP.NO_ADDRESS:
        if machine.ip_address_v6 in addresses["inet6"]:
            machine_.status_ipv6 = Machine.StatusIP.MAC_MISMATCH

    return machine_


def get_installations(fqdn: str) -> Union[bool, List[Installation]]:
    """Retrieve information of the installations."""
    try:
        machine = Machine.objects.get(fqdn=fqdn)
    except Machine.DoesNotExist:
        logger.warning("Machine '%s' does not exist", fqdn)
        return False

    conn = None

    timer = None
    try:
        conn = SSH(fqdn)
        conn.connect()
        timer = threading.Timer(5 * 60, conn.close)
        timer.start()

        # Installations
        logger.debug("Collect installations...")

        installations: List[Installation] = []
        script_execution = conn.execute_script_remote("machine_get_installations.sh")
        if script_execution:
            output, _, _ = script_execution
            for line in output:
                if line.startswith("--"):
                    installation = Installation(machine=machine)
                    installations.append(installation)
                elif line.startswith("ARCH="):
                    installation.architecture = line.split("=")[1].strip()  # type: ignore
                elif line.startswith("KERNEL="):
                    installation.kernelversion = line.split("=")[1].strip()  # type: ignore
                elif line.startswith("RUNNING="):
                    installation.active = line.startswith("RUNNING=1")  # type: ignore
                elif line.startswith("DIST="):
                    installation.distribution = line.split("=")[1].strip()  # type: ignore
                elif line.startswith("PART="):
                    installation.partition = line.split("=")[1].strip()  # type: ignore

        return installations

    except Exception as e:
        logger.exception("%s (%s)", fqdn, e)
        return False
    finally:
        if conn:
            conn.close()
        if timer:
            timer.cancel()


def get_pci_devices(fqdn: str) -> List["PCIDevice"]:
    """Retrieve all PCI devices."""

    def get_pci_device_by_slot(
        pci_devices: List["PCIDevice"], slot: str
    ) -> Optional["PCIDevice"]:
        """Return the PCI device by slot."""
        for dev in pci_devices:
            pci_slot = dev.slot
            if not pci_slot:
                continue
            pci_slot = pci_slot.strip()
            # pci domain hacks
            if len(pci_slot) < 8:
                pci_slot = "0000:" + pci_slot
            if len(slot) < 8:
                slot = "0000:" + slot
            if pci_slot == slot:
                return dev
        return None

    from orthos2.data.models import PCIDevice

    try:
        machine = Machine.objects.get(fqdn=fqdn)
    except Machine.DoesNotExist:
        logger.warning("Machine '%s' does not exist", fqdn)
        return False  # type: ignore

    logger.debug("Collect PCI devices for '%s'...", fqdn)
    pci_devices: List[PCIDevice] = []
    chunk = ""
    stdout, _, err = ssh_execute("lspci -mmvn", machine.fqdn)
    if err:
        logger.warning("Machine '%s' could not collect PCI devices", fqdn)
        return None  # type: ignore

    for line in stdout:
        if line.strip():
            chunk += line
        else:
            pci_devices.append(PCIDevice.from_lspci_mmnv(chunk))
            chunk = ""

    # drivers for PCI devices from hwinfo
    in_pci_device = False
    current_busid = None

    if machine.hwinfo:
        for line in machine.hwinfo.splitlines():
            if re.match(r"^\d+: PCI", line):
                in_pci_device = True
                continue
            if not line.strip():
                in_pci_device = False
                current_busid = None
                continue
            if not in_pci_device:
                continue
            match = re.match(r"  SysFS BusID: ([0-9a-fA-F.:]+)", line)
            if match:
                current_busid = match.group(1)
            match = re.match(r'  Driver: "([^"]*)"', line)
            if match and current_busid:
                pcidev = get_pci_device_by_slot(pci_devices, current_busid)
                if pcidev:
                    pcidev.drivermodule = match.group(1)
            match = re.match(r'  Driver Modules: "([^"]*)"', line)
            if match and current_busid:
                pcidev = get_pci_device_by_slot(pci_devices, current_busid)
                if pcidev:
                    pcidev.drivermodule = match.group(1)

    for pci_device in pci_devices:
        pci_device.machine = machine

    logger.debug("Collected %s PCI devices for '%s'", len(pci_devices), machine.fqdn)

    return pci_devices
