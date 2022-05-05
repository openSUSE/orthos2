import logging
import os
from datetime import date

from orthos2.utils.misc import get_random_mac_address

logger = logging.getLogger('models')


class VirtualizationAPI:

    class Type:
        LIBVIRT = 0

        @classmethod
        def to_str(cls, index):
            """Return type as string (Virtualization API type name) by index."""
            for type_tuple in VirtualizationAPI.TYPE_CHOICES:
                if int(index) == type_tuple[0]:
                    return type_tuple[1]
            raise Exception("Virtualization API type with ID '{}' doesn't exist!".format(index))

        @classmethod
        def to_int(cls, name):
            """Return type as integer if name matches."""
            for type_tuple in VirtualizationAPI.TYPE_CHOICES:
                if name.lower() == type_tuple[1].lower():
                    return type_tuple[0]
            raise Exception("Virtualization API type '{}' not found!".format(name))

    TYPE_CHOICES = (
        (Type.LIBVIRT, 'libvirt'),
    )

    def __init__(self, type, host, *args, **kwargs):
        """
        Cast plain `VirtualizationAPI` object to respective subclass.

        Subclasses getting collected automatically by inheritance of `VirtualizationAPI` class.
        """
        subclasses = {
            sub.__name__.replace(self.__class__.__name__, '').lower(): sub
            for sub in self.__class__.__subclasses__()
        }
        self._virtualizationapis = dict(
            map(lambda x: (
                x[0], {
                    'class': subclasses[x[1].lower().replace(' ', '').replace('/', '')],
                    'name': x[1]
                }), self.TYPE_CHOICES)
        )
        super(VirtualizationAPI, self).__init__(*args, **kwargs)

        self.type = type
        self.host = host

        self.__init__(*args, **kwargs)

    def _set_virtualization_api(self, type):
        """Set virtualization API type."""
        self.__class__ = self._virtualizationapis[type]['class']

    def __setattr__(self, attr, value):
        """If `type` attribute changes, set respective subclass."""
        # check for `None` explicitly because type 0 results in false
        if attr == 'type' and value is not None:
            self._set_virtualization_api(value)
        super(VirtualizationAPI, self).__setattr__(attr, value)

    def get_type(self):
        return self.type

    def get_image_list(self):
        raise NotImplementedError

    def create(self, *args, **kwargs):
        """
        Create a virtual machine.

        Method returns a new `Machine` object and calls the subclass to actually create the virtual
        machine physically.
        """
        from orthos2.data.models import (Architecture, Machine, RemotePower,
                                         SerialConsole, SerialConsoleType, System)
        from django.contrib.auth.models import User

        vm = Machine()
        vm.unsaved_networkinterfaces = []

        vm.architecture = Architecture.objects.get(name=kwargs['architecture'])
        vm.system = System.objects.get(pk=kwargs['system'])

        self._create(vm, *args, **kwargs)

        vm.mac_address = vm.unsaved_networkinterfaces[0].mac_address
        vm.check_connectivity = Machine.Connectivity.ALL
        vm.collect_system_information = True
        vm.save()

        for networkinterface in vm.unsaved_networkinterfaces[1:]:
            networkinterface.machine = vm
            networkinterface.save()
        vm.remotepower = RemotePower(fence_name="virsh")
        vm.remotepower.save()

        if self.host.has_serialconsole():
            stype = SerialConsoleType.objects.get(name='libvirt/qemu')
            if not stype:
                raise Exception("Bug: SerialConsoleType not found")
            vm.serialconsole = SerialConsole(
                stype=stype,
                baud_rate=115200
            )
            vm.serialconsole.save()

        if vm.vnc['enabled']:
            vm.annotations.create(
                text='VNC enabled: {}:{}'.format(self.host.fqdn, vm.vnc['port']),
                reporter=User.objects.get(username='admin')
            )

        return vm

    def remove(self, *args, **kwargs):
        return self._remove(*args, **kwargs)

    def get_list(self):
        raise NotImplementedError

    def __str__(self):
        return self.Type.to_str(self.type)

    def __repr__(self):
        return '<VirtualizationAPI: {} ({})>'.format(self, self.host.fqdn)


class Libvirt(VirtualizationAPI):

    class Meta:
        proxy = True

    VIRSH = 'virsh -c qemu:///system'
    IGNORE_STDERR = [
        'domain is not running',
        'no domain with matching name'
    ]
    QEMU_IMG_CONVERT = '/usr/bin/qemu-img convert -O qcow2 -o preallocation=metadata {0}.tmp {0}'

    def __init__(self):
        self.conn = None

    def get_image_list(self):
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
        image_directory = ServerConfig.objects.by_key('virtualization.libvirt.images.directory')
        image_list = []

        try:
            for architecture in architectures:
                directory = '{}/{}/'.format(image_directory.rstrip('/'), architecture)
                for image in os.listdir(directory):
                    path = directory + image
                    size = os.path.getsize(path)
                    atime = str(date.fromtimestamp(os.path.getmtime(path)))

                    if size < (1024**3):
                        size = int(size / (1024**2))
                        size = '{}M'.format(size)
                    else:
                        size = int(size / (1024**3))
                        size = '{}G'.format(size)

                    pretty_image = image.split('.')[0]

                    image_list.append((image, '{} ({} {})'.format(pretty_image, atime, size)))

        except FileNotFoundError as e:
            logger.exception(e)

        return (architectures, image_list)

    def connect(function):
        """Create SSH connection if needed."""
        def decorator(self, *args, **kwargs):
            from orthos2.utils.ssh import SSH

            if not self.conn:
                self.conn = SSH(self.host.fqdn)
                self.conn.connect()
            return function(self, *args, **kwargs)

        return decorator

    @connect
    def _execute(self, command):
        return self.conn.execute(command)

    def check_connection(self):
        """Check libvirt connection (running libvirt)."""
        _stdout, _stderr, exitstatus = self._execute('{} version'.format(self.VIRSH))
        if exitstatus == 0:
            return True
        return False

    def get_list(self, parameters='--all'):
        """Return `virsh list` output."""
        stdout, stderr, exitstatus = self._execute('{} list {}'.format(self.VIRSH, parameters))

        if exitstatus == 0:
            return ''.join(stdout)
        else:
            raise Exception(''.join(stderr))

        return False

    def check_network_bridge(self, bridge='br0'):
        """
        Execute `create_bridge.sh` script remotely and try to set up bridge if it doesn't exist.

        Returns true if the bridge is available, false otherwise.
        """
        stdout, stderr, exitstatus = self.conn.execute_script_remote('create_bridge.sh')

        if exitstatus != 0:
            raise Exception(''.join(stderr))

        stdout, stderr, exitstatus = self.conn.execute('bridge vlan')

        if exitstatus != 0:
            raise Exception(''.join(stderr))

        for line in stdout:
            if line.startswith(bridge):
                return True

        raise False

    def generate_hostname(self):
        """
        Generate domain name (hostname).

        Check hostnames against Orthos machines and libvirt `virsh list`.
        """
        hostname = None
        occupied_hostnames = {vm.hostname for vm in self.host.get_virtual_machines()}

        libvirt_list = self.get_list()
        for line in libvirt_list.split('\n')[2:]:
            columns = line.strip().split()
            if columns:
                domain_name = columns[1]
                occupied_hostnames.add(domain_name)

        for i in range(1, self.host.vm_max + 1):
            hostname_ = '{}-{}'.format(self.host.hostname, i)
            if hostname_ not in occupied_hostnames:
                hostname = hostname_
                break

        if hostname is None:
            raise Exception("All hostnames (domain names) busy!")

        return hostname

    def generate_networkinterfaces(self, amount=1, bridge='br0', model='virtio'):
        """Generate networkinterfaces."""
        from orthos2.data.models import NetworkInterface

        networkinterfaces = []
        for _i in range(amount):
            mac_address = get_random_mac_address()
            while NetworkInterface.objects.filter(mac_address=mac_address).count() != 0:
                mac_address = get_random_mac_address()

            networkinterface = NetworkInterface(mac_address=mac_address)
            networkinterface.bridge = bridge
            networkinterface.model = model

            networkinterfaces.append(networkinterface)

        return networkinterfaces

    def copy_image(self, image, disk_image):
        """Copy and allocate disk image."""
        _stdout, _stderr, exitstatus = self.conn.execute('cp {} {}.tmp'.format(image, disk_image))

        if exitstatus != 0:
            return False

        _stdout, _stderr, exitstatus = self.conn.execute(self.QEMU_IMG_CONVERT.format(disk_image))

        if exitstatus != 0:
            return False

        _stdout, _stderr, exitstatus = self.conn.execute('rm -rf {}.tmp'.format(disk_image))

        if exitstatus != 0:
            return False

        return True

    def delete_disk_image(self, disk_image):
        """Delete the old disk image."""
        _stdout, _stderr, exitstatus = self.conn.execute('rm -rf {}'.format(disk_image))

        if exitstatus != 0:
            return False

        return True

    def calculate_vcpu(self):
        """Return virtual CPU amount."""
        vcpu = 1

        host_cpu_cores = self.host.cpu_cores
        if host_cpu_cores is not None:
            vcpu = int((host_cpu_cores - 2) / self.host.vm_max)
            if vcpu == 0:
                vcpu = 1

        return vcpu

    def check_memory(self, memory_amount):
        """
        Check if memory amount for VM is available on host.

        Reserve 2GB of memory for host system.
        """
        host_ram_amount = self.host.ram_amount
        host_reserved_ram_amount = 2048

        if host_ram_amount:
            if memory_amount > (host_ram_amount - host_reserved_ram_amount):
                raise Exception("Host system has only {}MB of memory!".format(memory_amount))
        else:
            raise Exception("Can't detect memory size of host system '{}'".format(self.host))

        return True

    def execute_virt_install(self, *args, dry_run=True, **kwargs):
        """Run `virt-install` command."""
        command = '/usr/bin/virt-install '
        command += '--name {hostname} '
        command += '--vcpus {vcpu} '
        command += '--memory {memory} '
        command += '--osinfo detect=on,require=off '

        disk_ = '--disk {},'.format(kwargs['disk']['image'])
        disk_ += 'size={},'.format(kwargs['disk']['size'])
        disk_ += 'format={},'.format(kwargs['disk']['format'])
        disk_ += 'sparse={},'.format(kwargs['disk']['sparse'])
        disk_ += 'bus={} '.format(kwargs['disk']['bus'])
        command += disk_

        for networkinterface in kwargs.get('networkinterfaces', []):
            networkinterface_ = '--network model={},'.format(networkinterface.model)
            networkinterface_ += 'bridge={},'.format(networkinterface.bridge)
            networkinterface_ += 'mac={} '.format(networkinterface.mac_address)
            command += networkinterface_

        command += '{boot} '

        vnc = kwargs.get('vnc', None)
        if vnc and vnc['enabled']:
            command += '--graphics vnc,listen=0.0.0.0,port={} '.format(vnc['port'])

        command += kwargs.get('parameters', '')

        if dry_run:
            command += '--dry-run'

        command = command.format(**kwargs)
        logger.debug(command)
        _stdout, stderr, exitstatus = self.conn.execute(command)

        if exitstatus != 0:
            raise Exception(''.join(stderr))

        return True

    def _create(self, vm, *args, **kwargs):
        """
        Wrapper function for creating a VM.

        Steps:
            - check connection to host
            - check maxinmum VM number limit
            - check network bridge
            - check image source directory (if needed)
            - check Open Virtual Machine Firmware (OVMF) binary (if needed)
            - check memory size
            - generate hostname (=domain name)
            - copy image to disk image (if needed)
            - run `virt-install`
        """

        from orthos2.data.models import ServerConfig

        bridge = ServerConfig.objects.by_key('virtualization.libvirt.bridge')
        image_directory = ServerConfig.objects.by_key('virtualization.libvirt.images.directory')
        disk_image_directory = ServerConfig.objects.by_key('virtualization.libvirt.images.install_directory')
        disk_image = '{}/{}.qcow2'.format(disk_image_directory.rstrip('/'), '{}')
        ovmf = ServerConfig.objects.by_key('virtualization.libvirt.ovmf.path')

        image_directory = '{}/{}/'.format(
            image_directory.rstrip('/'),
            kwargs['architecture']
        )

        if not self.check_connection():
            raise Exception("Host system not reachable!")

        if self.host.get_virtual_machines().count() >= self.host.vm_max:
            raise Exception("Maximum number of VMs reached!")

        if not self.check_network_bridge(bridge=bridge):
            raise Exception("Network bridge setup failed!")

        if kwargs['image'] is not None:
            if not self.conn.check_path(image_directory, '-e'):
                raise Exception("Image source directory missing on host system!")

        if not self.conn.check_path(disk_image_directory, '-w'):
            _stdout, stderr, exitstatus = self._execute('mkdir -p {}'.format(disk_image_directory))
            if exitstatus != 0:
                raise Exception(
                    "Image disk directory {} could not get created on host system: {}!".format(
                        disk_image_directory, stderr)
            )
        if kwargs['uefi_boot']:
            if not self.conn.check_path(ovmf, '-e'):
                raise Exception("OVMF file not found: '{}'!".format(ovmf))
            boot = '--boot loader={},network,hd'.format(ovmf)
        else:
            boot = '--boot network,hd,menu=off,useserial=on'

        self.check_memory(kwargs['ram_amount'])

        vm.hostname = self.generate_hostname()
        vm.hypervisor = self.host
        vm.fqdn = '{}.{}'.format(vm.hostname, self.host.fqdn_domain.name)

        vnc_port = 5900 + int(vm.hostname.split('-')[1])
        vm.vnc = {
            'enabled': kwargs['vnc'],
            'port': vnc_port
        }

        vm.cpu_cores = self.calculate_vcpu()

        vm.ram_amount = kwargs['ram_amount']

        disk_image = disk_image.format(vm.hostname)

        if kwargs['image'] is not None:
            image = '{}/{}'.format(image_directory.rstrip('/'), kwargs['image'])

            if not self.copy_image(image, disk_image):
                raise Exception("Couldn't copy image: {} > {}!".format(image, disk_image))
        else:
            self.delete_disk_image(disk_image)

        disk = {
            'image': disk_image,
            'size': kwargs['disk_size'],
            'format': 'qcow2',
            'sparse': True,
            'bus': 'virtio'
        }

        networkinterfaces = self.generate_networkinterfaces(
            amount=kwargs['networkinterfaces'],
            bridge=bridge
        )

        parameters = '--events on_reboot=restart,on_poweroff=destroy '
        parameters += '--import '
        parameters += '--noautoconsole '
        parameters += '--autostart '
        parameters += kwargs['parameters']

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
            dry_run=False
        )

        vm.unsaved_networkinterfaces = []
        for networkinterface in networkinterfaces:
            vm.unsaved_networkinterfaces.append(networkinterface)

        return True

    def _remove(self, vm) -> bool:
        """Wrapper function for removing a VM (destroy domain > undefine domain).

        :return: Bool whether the VM could successfully be removed via virsh from Hypervisor
        """
        try:
            if not self.check_connection():
                raise Exception("Host system not reachable!")

            self.destroy(vm)
            self.undefine(vm)
        except Exception:
            logger.warning("Could not remove VM %s via from Hypervisor %s",
                           vm.hostname, self.host.fqdn)
            return False
        return True

    def destroy(self, vm):
        """Destroy VM on host system. Ignore `domain is not running` error and proceed."""
        _stdout, stderr, exitstatus = self._execute('{} destroy {}'.format(self.VIRSH, vm.hostname))
        if exitstatus != 0:
            stderr = ''.join(stderr)

            if not any(line in stderr for line in self.IGNORE_STDERR):
                raise Exception(stderr)

        return True

    def undefine(self, vm):
        """Undefine VM on host system."""
        _stdout, stderr, exitstatus = self._execute('{} undefine {}'.format(self.VIRSH, vm.hostname))
        if exitstatus != 0:
            stderr = ''.join(stderr)

            if not any(line in stderr for line in self.IGNORE_STDERR):
                raise Exception(stderr)

        return True
