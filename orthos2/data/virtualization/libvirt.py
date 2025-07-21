"""
Module to implement a virtualization API for libvirt.
"""

import logging
import os
from datetime import date
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Concatenate,
    Iterable,
    List,
    Optional,
    ParamSpec,
    Set,
    Tuple,
    TypeVar,
    Union,
)

from paramiko.channel import ChannelFile, ChannelStderrFile

from orthos2.data.virtualization import VirtualizationAPI
from orthos2.utils.misc import get_random_mac_address

if TYPE_CHECKING:
    from orthos2.data.models.machine import Machine
    from orthos2.data.models.networkinterface import NetworkInterface
    from orthos2.utils.ssh import SSH

logger = logging.getLogger("models")
P = ParamSpec("P")
R = TypeVar("R")


def connect(
    function: Callable[Concatenate["Libvirt", P], R],
) -> Callable[Concatenate["Libvirt", P], R]:
    """Create SSH connection if needed."""

    def decorator(self: "Libvirt", *args: P.args, **kwargs: P.kwargs) -> R:
        from orthos2.utils.ssh import SSH

        if not self.conn:
            self.conn = SSH(self.host.fqdn)
            self.conn.connect()
        return function(self, *args, **kwargs)

    return decorator


class Libvirt(VirtualizationAPI):
    class Meta:
        proxy = True

    VIRSH = "virsh -c qemu:///system"
    IGNORE_STDERR = ["domain is not running", "no domain with matching name"]
    QEMU_IMG_CONVERT = (
        "/usr/bin/qemu-img convert -O qcow2 -o preallocation=metadata {0}.tmp {0}"
    )

    def __init__(self, host: "Machine") -> None:
        """
        Constructor to initate the libvirt virtualization API.
        """
        super().__init__(VirtualizationAPI.Type.LIBVIRT, host)
        self.conn: Optional["SSH"] = None

    def get_image_list(self) -> Tuple[List[str], List[Tuple[str, str]]]:
        """
        Return the available architectures and the full image list (over all available
        architectures).

        Return format:
            (
                ['<arch1>', '<arch2>', ...], [('<value>', '<option>'), ...]
            )
        """
        from orthos2.data.models import ServerConfig

        architectures = [self.host.architecture.name]
        image_directory = ServerConfig.get_server_config_manager().by_key(
            "virtualization.libvirt.images.directory", "/var/lib/libvirt/images"
        )
        image_list: List[Tuple[str, str]] = []
        if image_directory is None:
            raise ValueError(
                'ServerConfig key "virtualization.libvirt.images.directory" cannot be None'
            )

        try:
            for architecture in architectures:
                directory = "{}/{}/".format(image_directory.rstrip("/"), architecture)
                for image in os.listdir(directory):
                    path = directory + image
                    size = os.path.getsize(path)
                    atime = str(date.fromtimestamp(os.path.getmtime(path)))

                    if size < (1024**3):
                        size = int(size / (1024**2))
                        human_size = f"{size}M"
                    else:
                        size = int(size / (1024**3))
                        human_size = f"{size}G"

                    pretty_image = image.split(".")[0]

                    image_list.append(
                        (image, "{} ({} {})".format(pretty_image, atime, human_size))
                    )

        except FileNotFoundError as e:
            logger.exception(e)

        return architectures, image_list

    @connect
    def _execute(
        self, command: str
    ) -> Tuple[
        Union[Iterable[str], ChannelFile], Union[Iterable[str], ChannelStderrFile], int
    ]:
        if self.conn is None:
            raise Exception("Connection not established")
        return self.conn.execute(command)

    def check_connection(self) -> bool:
        """Check libvirt connection (running libvirt)."""
        _stdout, _stderr, exitstatus = self._execute("{} version".format(self.VIRSH))
        if exitstatus == 0:
            return True
        return False

    def get_list(self, parameters: str = "--all") -> str:
        """Return `virsh list` output."""
        stdout, stderr, exitstatus = self._execute(
            "{} list {}".format(self.VIRSH, parameters)
        )

        if exitstatus == 0:
            return "".join(stdout)
        raise Exception("".join(stderr))

    def check_network_bridge(self, bridge: str = "br0") -> bool:
        """
        Execute `create_bridge.sh` script remotely and try to set up bridge if it doesn't exist.

        Returns true if the bridge is available, false otherwise.
        """
        if self.conn is None:
            raise Exception("Connection not established")

        script_result = self.conn.execute_script_remote("create_bridge.sh")

        if script_result is None:
            raise Exception("No script result retrieved!")
        stdout, stderr, exitstatus = script_result

        if exitstatus != 0:
            raise Exception("".join(stderr))

        stdout, stderr, exitstatus = self.conn.execute("bridge vlan")

        if exitstatus != 0:
            raise Exception("".join(stderr))

        for line in stdout:
            if line.startswith(bridge):
                return True

        return False

    def generate_hostname(self) -> Optional[str]:
        """
        Generate domain name (hostname).

        Check hostnames against Orthos machines and libvirt `virsh list`.
        """
        hostname = None
        occupied_hostnames: Set[Optional[str]] = set()
        virtual_machines = self.host.get_virtual_machines()
        if virtual_machines is not None:
            occupied_hostnames = {vm.hostname for vm in virtual_machines}

        libvirt_list = self.get_list()
        for line in libvirt_list.split("\n")[2:]:
            columns = line.strip().split()
            if columns:
                domain_name = columns[1]
                occupied_hostnames.add(domain_name)

        for i in range(1, self.host.vm_max + 1):
            hostname_ = "{}-{}".format(self.host.hostname, i)
            if hostname_ not in occupied_hostnames:
                hostname = hostname_
                break

        if hostname is None:
            raise Exception("All hostnames (domain names) busy!")

        return hostname

    def generate_networkinterfaces(
        self, amount: int = 1, bridge: str = "br0", model: str = "virtio"
    ) -> List["NetworkInterface"]:
        """Generate networkinterfaces."""
        from orthos2.data.models import NetworkInterface

        networkinterfaces: List[NetworkInterface] = []
        for _i in range(amount):
            mac_address = get_random_mac_address()
            while NetworkInterface.objects.filter(mac_address=mac_address).count() != 0:
                mac_address = get_random_mac_address()

            networkinterface = NetworkInterface(mac_address=mac_address)
            networkinterface.bridge = bridge
            networkinterface.model = model

            networkinterfaces.append(networkinterface)

        return networkinterfaces

    def copy_image(self, image: str, disk_image: str) -> bool:
        """Copy and allocate disk image."""
        if self.conn is None:
            raise Exception("Connection not established")

        _stdout, _stderr, exitstatus = self.conn.execute(
            "cp {} {}.tmp".format(image, disk_image)
        )

        if exitstatus != 0:
            return False

        _stdout, _stderr, exitstatus = self.conn.execute(
            self.QEMU_IMG_CONVERT.format(disk_image)
        )

        if exitstatus != 0:
            return False

        _stdout, _stderr, exitstatus = self.conn.execute(
            "rm -rf {}.tmp".format(disk_image)
        )

        if exitstatus != 0:
            return False

        return True

    def delete_disk_image(self, disk_image: str) -> bool:
        """Delete the old disk image."""
        if self.conn is None:
            raise Exception("Connection not established")

        _stdout, _stderr, exitstatus = self.conn.execute("rm -rf {}".format(disk_image))

        if exitstatus != 0:
            return False

        return True

    def calculate_vcpu(self) -> int:
        """Return virtual CPU amount."""
        vcpu = 1

        host_cpu_cores = self.host.cpu_cores

        vcpu = int((host_cpu_cores - 2) / self.host.vm_max)
        if vcpu == 0:
            vcpu = 1

        return vcpu

    def check_memory(self, memory_amount: int) -> bool:
        """
        Check if memory amount for VM is available on host.

        Reserve 2GB of memory for host system.
        """
        host_ram_amount = self.host.ram_amount
        host_reserved_ram_amount = 2048

        if host_ram_amount:
            if memory_amount > (host_ram_amount - host_reserved_ram_amount):
                raise Exception(
                    "Host system has only {}MB of memory!".format(memory_amount)
                )
        else:
            raise Exception(
                "Can't detect memory size of host system '{}'".format(self.host)
            )

        return True

    def execute_virt_install(
        self, *args: Any, dry_run: bool = True, **kwargs: Any
    ) -> bool:
        """Run `virt-install` command."""
        command = "/usr/bin/virt-install "
        command += "--name {hostname} "
        command += "--vcpus {vcpu} "
        command += "--memory {memory} "
        command += "--osinfo detect=on,require=off "

        disk_ = "--disk {},".format(kwargs["disk"]["image"])
        disk_ += "size={},".format(kwargs["disk"]["size"])
        disk_ += "format={},".format(kwargs["disk"]["format"])
        disk_ += "sparse={},".format(kwargs["disk"]["sparse"])
        disk_ += "bus={} ".format(kwargs["disk"]["bus"])
        command += disk_

        for networkinterface in kwargs.get("networkinterfaces", []):
            networkinterface_ = "--network model={},".format(networkinterface.model)
            networkinterface_ += "bridge={},".format(networkinterface.bridge)
            networkinterface_ += "mac={} ".format(networkinterface.mac_address)
            command += networkinterface_

        command += "{boot} "

        vnc = kwargs.get("vnc", None)
        if vnc and vnc["enabled"]:
            command += "--graphics vnc,listen=0.0.0.0,port={} ".format(vnc["port"])

        command += kwargs.get("parameters", "")

        if dry_run:
            command += "--dry-run"

        command = command.format(**kwargs)
        if self.conn is None:
            raise Exception("Connection not established")
        logger.debug(command)
        _stdout, stderr, exitstatus = self.conn.execute(command)

        if exitstatus != 0:
            raise Exception("".join(stderr))

        return True

    def _create(self, vm: "Machine", *args: Any, **kwargs: Any) -> bool:
        """
        Wrapper function for creating a VM.

        Steps:
            - check connection to host
            - check maximum VM number limit
            - check network bridge
            - check image source directory (if needed)
            - check Open Virtual Machine Firmware (OVMF) binary (if needed)
            - check memory size
            - generate hostname (=domain name)
            - copy image to disk image (if needed)
            - run `virt-install`
        """
        from orthos2.data.models import ServerConfig

        if self.conn is None:
            raise Exception("Connection not established")

        bridge = ServerConfig.get_server_config_manager().by_key(
            "virtualization.libvirt.bridge"
        )
        image_directory = ServerConfig.get_server_config_manager().by_key(
            "virtualization.libvirt.images.directory"
        )
        disk_image_directory = ServerConfig.get_server_config_manager().by_key(
            "virtualization.libvirt.images.install_directory"
        )
        ovmf = ServerConfig.get_server_config_manager().by_key(
            "virtualization.libvirt.ovmf.path"
        )

        if bridge is None:
            raise RuntimeError(
                'The ServerConfig variable "virtualization.libvirt.bridge" cannot be undefined!'
            )

        if image_directory is None:
            raise RuntimeError(
                'The ServerConfig variable "virtualization.libvirt.images.directory" cannot be undefined!'
            )

        if disk_image_directory is None:
            raise RuntimeError(
                'The ServerConfig variable "virtualization.libvirt.images.install_directory" cannot be undefined!'
            )

        if ovmf is None:
            raise RuntimeError(
                'The ServerConfig variable "virtualization.libvirt.ovmf.path" cannot be undefined!'
            )

        disk_image = "{}/{}.qcow2".format(disk_image_directory.rstrip("/"), "{}")

        image_directory = "{}/{}/".format(
            image_directory.rstrip("/"), kwargs["architecture"]
        )

        if not self.check_connection():
            raise Exception("Host system not reachable!")

        virtual_machines = self.host.get_virtual_machines()
        if virtual_machines is None:
            raise Exception(f'Could not get VMs for hypervisor "{self.host.fqdn}"!')

        if virtual_machines.count() >= self.host.vm_max:
            raise Exception("Maximum number of VMs reached!")

        if not self.check_network_bridge(bridge=bridge):
            raise Exception("Network bridge setup failed!")

        if kwargs["image"] is not None:
            if not self.conn.check_path(image_directory, "-e"):
                raise Exception("Image source directory missing on host system!")

        if not self.conn.check_path(disk_image_directory, "-w"):
            _stdout, stderr, exitstatus = self._execute(
                "mkdir -p {}".format(disk_image_directory)
            )
            if exitstatus != 0:
                raise Exception(
                    "Image disk directory {} could not get created on host system: {}!".format(
                        disk_image_directory, stderr
                    )
                )
        if kwargs["uefi_boot"]:
            if not self.conn.check_path(ovmf, "-e"):
                raise Exception("OVMF file not found: '{}'!".format(ovmf))
            boot = "--boot loader={},network,hd".format(ovmf)
        else:
            boot = "--boot network,hd,menu=off,useserial=on"

        self.check_memory(kwargs["ram_amount"])

        vm.hypervisor = self.host
        vm.fqdn = "{}.{}".format(self.generate_hostname(), self.host.fqdn_domain.name)

        vnc_port = 5900 + int(vm.hostname.split("-")[1])
        vm.vnc = {"enabled": kwargs["vnc"], "port": vnc_port}

        vm.cpu_cores = self.calculate_vcpu()

        vm.ram_amount = kwargs["ram_amount"]

        disk_image = disk_image.format(vm.hostname)

        if kwargs["image"] is not None:
            image = "{}/{}".format(image_directory.rstrip("/"), kwargs["image"])

            if not self.copy_image(image, disk_image):
                raise Exception(
                    "Couldn't copy image: {} > {}!".format(image, disk_image)
                )
        else:
            self.delete_disk_image(disk_image)

        disk = {
            "image": disk_image,
            "size": kwargs["disk_size"],
            "format": "qcow2",
            "sparse": True,
            "bus": "virtio",
        }

        networkinterfaces = self.generate_networkinterfaces(
            amount=kwargs["networkinterfaces"], bridge=bridge
        )

        parameters = "--events on_reboot=restart,on_poweroff=destroy "
        parameters += "--import "
        parameters += "--noautoconsole "
        parameters += "--autostart "
        parameters += kwargs["parameters"]

        self.execute_virt_install(
            hostname=vm.hostname,
            vcpu=vm.cpu_cores,
            memory=vm.ram_amount,
            disk=disk,
            networkinterfaces=networkinterfaces,
            boot=boot,
            vnc=vm.vnc,
            parameters=parameters,
        )

        self.execute_virt_install(
            hostname=vm.hostname,
            vcpu=vm.cpu_cores,
            memory=vm.ram_amount,
            disk=disk,
            networkinterfaces=networkinterfaces,
            boot=boot,
            vnc=vm.vnc,
            parameters=parameters,
            dry_run=False,
        )

        vm.unsaved_networkinterfaces = networkinterfaces

        return True

    def _remove(self, vm: "Machine") -> bool:
        """Wrapper function for removing a VM (destroy domain > undefine domain).

        :return: Bool whether the VM could successfully be removed via virsh from Hypervisor
        """
        try:
            if not self.check_connection():
                raise Exception("Host system not reachable!")

            self.destroy(vm)
            self.undefine(vm)
        except Exception:
            logger.warning(
                "Could not remove VM %s via from Hypervisor %s",
                vm.hostname,
                self.host.fqdn,
            )
            return False
        return True

    def destroy(self, vm: "Machine") -> bool:
        """Destroy VM on host system. Ignore `domain is not running` error and proceed."""
        _stdout, stderr, exitstatus = self._execute(
            "{} destroy {}".format(self.VIRSH, vm.hostname)
        )
        if exitstatus != 0:
            stderr = "".join(stderr)

            if not any(line in stderr for line in self.IGNORE_STDERR):
                raise Exception(stderr)

        return True

    def undefine(self, vm: "Machine") -> bool:
        """Undefine VM on host system."""
        _stdout, stderr, exitstatus = self._execute(
            "{} undefine {}".format(self.VIRSH, vm.hostname)
        )
        if exitstatus != 0:
            stderr = "".join(stderr)

            if not any(line in stderr for line in self.IGNORE_STDERR):
                raise Exception(stderr)

        return True
