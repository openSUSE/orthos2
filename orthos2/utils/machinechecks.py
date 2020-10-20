import logging
import re
import socket
import threading
from decimal import Decimal

from orthos2.data.models import Architecture, Installation, Machine, NetworkInterface
from orthos2.utils.misc import execute, normalize_ascii
from orthos2.utils.ssh import SSH

ARPHRD_IEEE80211 = 801

logger = logging.getLogger('utils')


def ping_check(fqdn, timeout=None, ip_version=4):
    """Check if the server pings."""
    command = '/usr/bin/ping'
    if ip_version == 6:
        command = '/usr/bin/ping6'

    if timeout is None:
        stdout, stderr, returncode = execute('{} -c1 -q {}'.format(command, fqdn))
    else:
        stdout, stderr, returncode = execute('{} -W{} -c1 -q {}'.format(command, timeout, fqdn))

    return returncode == 0


def ping_check_ipv4(fqdn, timeout):
    return ping_check(fqdn, timeout, ip_version=4)


def ping_check_ipv6(fqdn, timeout):
    return ping_check(fqdn, timeout, ip_version=6)


def nmap_check(fqdn):
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


def login_test(fqdn):
    """Check if it's possible to login via SSH."""
    conn = None
    try:
        conn = SSH(fqdn)
        conn.connect()
    except Exception as e:
        logger.warning("SSH login failed for '{}': {}".format(fqdn, e))
        return False
    finally:
        if conn:
            conn.close()

    return True


def abuild_test(fqdn):
    """Check if Autobuild is running."""
    conn = None
    try:
        conn = SSH(fqdn)
        conn.connect()
        pids, stderr, exitstatus = conn.execute(
            r"ps -e -o pid,cmd | awk '/.*\/usr\/sbin\/autobuild.*/{print $1}'"
        )
        if pids:
            return True
    except Exception as e:
        logger.warning("SSH login failed for '{}': {}".format(fqdn, e))
        return False
    finally:
        if conn:
            conn.close()

    return False


def get_hardware_information(fqdn):
    """Retrieve information of the system."""
    try:
        machine = Machine.objects.get(fqdn=fqdn)
    except Machine.DoesNotExist:
        logger.warning("Machine '{}' does not exist".format(fqdn))
        return

    # set needed values for several checks from original machine
    machine_ = Machine(
        architecture=machine.architecture
    )

    conn = None
    timer = None
    try:
        conn = SSH(fqdn)
        conn.connect()
        timer = threading.Timer(5 * 60, conn.close)
        timer.start()

        # CPUs
        logger.debug("Get CPU number...")
        output, stderr, exitstatus = conn.execute_script_remote('machine_get_cpu_number.sh')
        if output:
            for line in output:
                if line.startswith('SOCKETS'):
                    machine_.cpu_physical = int(line.split('=')[1])
                elif line.startswith('CORES'):
                    machine_.cpu_cores = int(line.split('=')[1])
                elif line.startswith('THREADS'):
                    machine_.cpu_threads = int(line.split('=')[1])

        logger.debug("Get CPU type...")
        output, stderr, exitstatus = conn.execute_script_remote('machine_get_cpu_type.sh')
        if output and output[0]:
            machine_.cpu_model = output[0].strip()

        logger.debug("Get CPU flags...")
        output, stderr, exitstatus = conn.execute_script_remote('machine_get_cpu_flags.sh')
        if output and output[0]:
            machine_.cpu_flags = output[0].strip()

        logger.debug("Get CPU speed...")
        output, stderr, exitstatus = conn.execute_script_remote('machine_get_cpu_speed.sh')
        if output and output[0]:
            machine_.cpu_speed = Decimal(int(output[0].strip()) / 1000000)

        logger.debug("Get CPU ID...")
        output, stderr, exitstatus = conn.execute_script_remote('machine_get_cpu_id.sh')
        if output and output[0]:
            machine_.cpu_id = output[0].strip()

        # EFI
        logger.debug("Check for EFI...")
        try:
            efi_file = conn.get_file('/sys/firmware/efi', 'r')
            efi_file.close()
            machine_.efi = True
        except IOError:
            machine_.efi = False

        # Memory
        logger.debug("Get RAM amount...")
        for line in conn.read_file('/proc/meminfo'):
            if line.startswith('MemTotal'):
                machine_.ram_amount = int(int(line.split()[1]) / 1024)

        # Virtualization capability
        VM_HOST_MIN_RAM_MB = 7000
        machine_.vm_capable = False

        # Virtualization: x86
        logger.debug("Check for VM capability...")
        if machine_.architecture_id == Architecture.Type.X86_64:
            cpu_flags = machine_.cpu_flags
            if cpu_flags:
                cpu_flags = cpu_flags.upper()
                if ((cpu_flags.find('VMX') >= 0 or cpu_flags.find('SVM') >= 0) and
                        int(machine_.ram_amount) > VM_HOST_MIN_RAM_MB):
                    machine_.vm_capable = True

        # Virtualization: ppc64le
        if machine_.architecture_id == Architecture.Type.PPC64LE:
            for line in conn.read_file('/proc/cpuinfo'):
                if line.startswith('firmware') and 'OPAL' in line:
                    machine_.vm_capable = True

        # Disk
        logger.debug("Get disk information...")
        stdout, stderr, exitstatus = conn.execute('hwinfo --disk')
        for line in stdout:
            line = line.strip()
            if line.startswith('Size:'):
                machine_.disk_primary_size = int(int(line.split()[1]) / 2 / 1024 ** 2)
            elif line.startswith('Attached to:'):
                opening_bracket = line.find('(')
                closing_bracket = line.find(')')
                if opening_bracket > 0 and closing_bracket > 0:
                    machine_.disk_type = line[opening_bracket + 1:closing_bracket]
                else:
                    machine_.disk_type = 'Unknown disk type'
                break

        # lsmod
        logger.debug("Get 'lsmod'...")
        stdout, stderr, exitstatus = conn.execute('lsmod')
        machine_.lsmod = normalize_ascii("".join(stdout))

        # lspci
        logger.debug("Get 'lspci'...")
        stdout, stderr, exitstatus = conn.execute('lspci -vvv -nn')
        machine_.lspci = normalize_ascii("".join(stdout))

        # last
        logger.debug("Get 'last'...")
        output, stderr, exitstatus = conn.execute('last | grep -v reboot | head -n 1')
        string = ''.join(output)
        result = string[0:8] + string[38:49]
        machine_.last = normalize_ascii("".join(result))

        # hwinfo
        logger.debug("Get 'hwinfo' (full)...")
        stdout, stderr, exitstatus = conn.execute(
            'hwinfo --bios ' +
            '--block --bridge --cdrom --cpu --disk --floppy --framebuffer ' +
            '--gfxcard --hub --ide --isapnp --isdn --keyboard --memory ' +
            '--monitor --mouse --netcard --network --partition --pci --pcmcia ' +
            '--scsi --smp --sound --sys --tape --tv --usb --usb-ctrl --wlan'
        )
        machine_.hwinfo = normalize_ascii("".join(stdout))

        # dmidecode
        logger.debug("Get 'dmidecode'...")
        stdout, stderr, exitstatus = conn.execute('dmidecode')
        machine_.dmidecode = normalize_ascii("".join(stdout))

        # dmesg
        logger.debug("Get 'dmesg'...")
        stdout, stderr, exitstatus = conn.execute(
            'if [ -e /var/log/boot.msg ]; then ' +
            'cat /var/log/boot.msg; else journalctl -xl | head -n200; ' +
            'fi'
        )
        machine_.dmesg = normalize_ascii("".join(stdout))

        # lsscsi
        logger.debug("Get 'lsscsi'...")
        stdout, stderr, exitstatus = conn.execute('lsscsi -s')
        machine_.lsscsi = normalize_ascii("".join(stdout))

        # lsusb
        logger.debug("Get 'lsusb'...")
        stdout, stderr, exitstatus = conn.execute('lsusb')
        machine_.lsusb = normalize_ascii("".join(stdout))

        # IPMI
        logger.debug("Check for IPMI...")
        machine_.ipmi = machine_.dmidecode.find('IPMI') >= 0

        # Firmware script
        logger.debug("Get BIOS version...")
        output, stderr, exitstatus = conn.execute_script_remote('machine_get_firmware.sh')
        if output and output[0]:
            machine_.bios_version = output[0].strip()

        return machine_

    except Exception as e:
        logger.error("{} ({})".format(fqdn, e))
        return False
    finally:
        if conn:
            conn.close()
        if timer:
            timer.cancel()

    return None


def get_networkinterfaces(fqdn):
    """Retrieve information of the systems network interfaces."""
    try:
        machine = Machine.objects.get(fqdn=fqdn)
    except Machine.DoesNotExist:
        logger.warning("Machine '{}' does not exist".format(fqdn))
        return False

    conn = None
    timer = None
    try:
        conn = SSH(machine.fqdn)
        conn.connect()
        timer = threading.Timer(5 * 60, conn.close)
        timer.start()

        # Network interfaces
        logger.debug("Collect network interfaces...")
        stdout, stderr, exitstatus = conn.execute('hwinfo --network')
        interfaces = []
        interface = None

        for line in stdout:
            if line and line[0] != ' ' and line[0] != '\t':
                if interface and interface.mac_address and\
                        interface.driver_module not in {'bridge', 'tun'}:

                    interfaces.append(interface)
                interface = NetworkInterface()
            else:
                match = re.match(r'\s+Driver: "(\w+)"', line)
                if match:
                    interface.driver_module = match.group(1)
                    continue

                match = re.match(r'\s+SysFS ID: ([/\w.]+)', line)
                if match:
                    interface.sysfs = match.group(1)
                    continue

                match = re.match(r'\s+HW Address: ([0-9a-fA-F:]+)', line)
                if match:
                    interface.mac_address = match.group(1).upper()
                    continue

                match = re.match(r'\s+Device File: ([\w.]+)', line)
                if match:
                    interface.name = match.group(1)
                    continue

        if interface and interface.mac_address and\
                interface.driver_module not in {'bridge', 'tun'}:

            interfaces.append(interface)

        for interface in interfaces:
            if interface.sysfs is None:
                continue

            path = '/sys/{}/type'.format(interface.sysfs)
            arp_type = ''.join(conn.read_file(path))

            if arp_type == ARPHRD_IEEE80211:
                continue

            stdout, stderr, exitstatus = conn.execute('ethtool {}'.format(interface.name))
            for line in stdout:
                match = re.match(r'\s+Port: (.+)', line)
                if match:
                    interface.ethernet_type = match.group(1)

        return interfaces

    except Exception as e:
        logger.error("{} ({})".format(fqdn, e))
        return False
    finally:
        if conn:
            conn.close()
        if timer:
            timer.cancel()

    return None


def get_status_ip(fqdn):
    """Retrieve information of the systems IPv4/IPv6 status."""
    try:
        machine = Machine.objects.get(fqdn=fqdn)
    except Machine.DoesNotExist:
        logger.warning("Machine '{}' does not exist".format(fqdn))
        return False

    machine_ = Machine()

    conn = None
    timer = None
    try:
        conn = SSH(machine.fqdn)
        conn.connect()
        timer = threading.Timer(5 * 60, conn.close)
        timer.start()

        logger.debug("Check IPv4/IPv6 status...")
        stdout, stderr, exitstatus = conn.execute('/sbin/ip a')

        devices = {}
        current_device = None
        addresses = {'inet': [], 'inet6': []}

        for line in stdout:
            match = re.match(r'^\d+:\s+([a-zA-Z0-9]+):\s+<.*>\s(.*)\n', line)
            if match:
                current_device = match.group(1)
                devices[current_device] = {
                    'mac_address': None,
                    'inet': None,
                    'inet6': None,
                    'flags': None
                }
                devices[current_device]['flags'] = match.group(2).split()
                continue

            line = line.lstrip()

            match = re.match(r'inet ([0-9.]{7,15})\/.*scope', line)
            if match:
                if devices[current_device]['inet'] is None:
                    devices[current_device]['inet'] = []
                devices[current_device]['inet'].append(match.group(1))
                continue

            match = re.match(r'inet6 ([a-f0-9:]*)\/[0-9]+ scope', line)
            if match:
                if devices[current_device]['inet6'] is None:
                    devices[current_device]['inet6'] = []
                devices[current_device]['inet6'].append(match.group(1))
                continue

            match = re.match('link/ether ([a-f0-9:]{17}) brd', line)
            if match:
                devices[current_device]['mac_address'] = match.group(1).upper()

        for device, values in devices.items():
            if values['mac_address'] is None:
                continue

            # ignore device if hooking up another
            if any(device in values['flags'] for device in devices.keys()):
                continue

            if values['mac_address'] == machine.mac_address:
                if values['inet'] is None:
                    machine_.status_ipv4 = Machine.StatusIP.AF_DISABLED
                elif machine.ipv4 not in values['inet']:
                    machine_.status_ipv4 = Machine.StatusIP.NO_ADDRESS
                    if [ipv4 for ipv4 in values['inet'] if not ipv4.startswith('127.0.0.1')]:
                        machine_.status_ipv4 = Machine.StatusIP.ADDRESS_MISMATCH
                elif machine.ipv4 in values['inet']:
                    machine_.status_ipv4 = Machine.StatusIP.CONFIRMED
                else:
                    machine_.status_ipv4 = Machine.StatusIP.MISSING

                if values['inet6'] is None:
                    machine_.status_ipv6 = Machine.StatusIP.AF_DISABLED
                elif machine.ipv6 not in values['inet6']:
                    machine_.status_ipv6 = Machine.StatusIP.NO_ADDRESS
                    if [ipv6 for ipv6 in values['inet6'] if not ipv6.startswith('fe80::')]:
                        machine_.status_ipv6 = Machine.StatusIP.ADDRESS_MISMATCH
                elif machine.ipv6 in values['inet6']:
                    machine_.status_ipv6 = Machine.StatusIP.CONFIRMED

            addresses['inet'].append(values['inet'])
            addresses['inet6'].append(values['inet6'])

        if machine_.status_ipv4 == Machine.StatusIP.NO_ADDRESS:
            if machine.ipv4 in addresses['inet']:
                machine_.status_ipv4 = Machine.StatusIP.MAC_MISMATCH

        if machine_.status_ipv6 == Machine.StatusIP.NO_ADDRESS:
            if machine.ipv6 in addresses['inet6']:
                machine_.status_ipv6 = Machine.StatusIP.MAC_MISMATCH

        return machine_

    except Exception as e:
        logger.error("{} ({})".format(fqdn, e))
        return False
    finally:
        if conn:
            conn.close()
        if timer:
            timer.cancel()

    return None


def get_installations(fqdn):
    """Retrieve information of the installations."""
    try:
        machine = Machine.objects.get(fqdn=fqdn)
    except Machine.DoesNotExist:
        logger.warning("Machine '{}' does not exist".format(fqdn))
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

        installations = []
        output, stderr, exitstatus = conn.execute_script_remote('machine_get_installations.sh')
        if output:
            for line in output:
                if line.startswith('--'):
                    installation = Installation(machine=machine)
                    installations.append(installation)
                elif line.startswith('ARCH='):
                    installation.architecture = line.split('=')[1].strip()
                elif line.startswith('KERNEL='):
                    installation.kernelversion = line.split('=')[1].strip()
                elif line.startswith('RUNNING='):
                    installation.active = line.startswith('RUNNING=1')
                elif line.startswith('DIST='):
                    installation.distribution = line.split('=')[1].strip()
                elif line.startswith('PART='):
                    installation.partition = line.split('=')[1].strip()

        return installations

    except Exception as e:
        logger.error("{} ({})".format(fqdn, e))
        return False
    finally:
        if conn:
            conn.close()
        if timer:
            timer.cancel()

    return None


def get_pci_devices(fqdn):
    """Retrieve all PCI devices."""

    def get_pci_device_by_slot(pci_devices, slot):
        """Return the PCI device by slot."""
        for dev in pci_devices:
            pci_slot = dev.slot
            if not pci_slot:
                continue
            pci_slot = pci_slot.strip()
            # pci domain hacks
            if len(pci_slot) < 8:
                pci_slot = '0000:' + pci_slot
            if len(slot) < 8:
                slot = '0000:' + slot
            if pci_slot == slot:
                return dev
        return None

    from orthos2.data.models import PCIDevice

    try:
        machine = Machine.objects.get(fqdn=fqdn)
    except Machine.DoesNotExist:
        logger.warning("Machine '{}' does not exist".format(fqdn))
        return False

    conn = None
    timer = None
    try:
        conn = SSH(fqdn)
        conn.connect()
        timer = threading.Timer(5 * 60, conn.close)
        timer.start()

        logger.debug("Collect PCI devices for '{}'...".format(machine.fqdn))
        pci_devices = []
        chunk = ''
        stdout, stderr, exitstatus = conn.execute('lspci -mmvn')
        for line in stdout:
            if line.strip():
                chunk += line
            else:
                pci_devices.append(PCIDevice.from_lspci_mmnv(chunk))
                chunk = ''

        # drivers for PCI devices from hwinfo
        in_pci_device = False
        current_busid = None

        if machine.hwinfo:
            for line in machine.hwinfo.splitlines():
                if re.match(r'^\d+: PCI', line):
                    in_pci_device = True
                    continue
                if not line.strip():
                    in_pci_device = False
                    current_busid = None
                    continue
                if not in_pci_device:
                    continue
                match = re.match(r'  SysFS BusID: ([0-9a-fA-F.:]+)', line)
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

        logger.debug("Collected {} PCI devices for '{}'".format(len(pci_devices), machine.fqdn))

        return pci_devices

    except Exception as e:
        logger.exception("{} ({})".format(fqdn, e))
        return False
    finally:
        if conn:
            conn.close()
        if timer:
            timer.cancel()
