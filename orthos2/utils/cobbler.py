import logging

from django.template import Context, Template

from orthos2.data.models import Machine, ServerConfig
from orthos2.utils.ssh import SSH
from orthos2.utils.misc import get_hostname, get_ipv4, get_ipv6
from orthos2.utils.remotepowertype import RemotePowerType

logger = logging.getLogger('utils')


class CobblerException(Exception):
    pass


def get_default_profile(machine):
    default = machine.architecture.default_profile
    if default:
        return default
    raise ValueError("Machine {machine} has no default profile".format(machine=machine.fqdn))


def get_tftp_server(machine: Machine):
    """
    Return the corresponding tftp server attribute for the DHCP record.

    Machine > Group > Domain
    """

    if machine.tftp_server:
        server = machine.tftp_server
    elif machine.group and machine.group.tftp_server:
        server = machine.group.tftp_server
    elif machine.fqdn_domain.tftp_server:
        server = machine.fqdn_domain.tftp_server
    else:
        server = None
    return server.fqdn if server else None


def create_cobbler_options(machine):
    tftp_server = get_tftp_server(machine)
    kernel_options = machine.kernel_options if machine.kernel_options else ""
    options = " --name={name} --ip-address={ipv4}".format(name=machine.fqdn, ipv4=machine.ipv4)
    options += " --hostname={host} ".format(host=get_hostname(machine.fqdn))
    if machine.mac_address:
        options += " --interface=default --management=True --interface-master=True"
        options += " --dns-name={dns} ".format(dns=machine.fqdn)
        options += " --mac-address={mac} ".format(mac=machine.mac_address)
        options += " --ipv6-address={ipv6}".format(ipv6=machine.ipv6 or '')
    options += " --filename={filename}".format(filename=get_filename(machine) or '')
    if tftp_server:
        ipv4 = get_ipv4(tftp_server)
        if ipv4:
            options += " --next-server-v4={server}".format(server=ipv4)
    if machine.has_remotepower():
        options += get_power_options(machine)
    if machine.has_serialconsole():
        serial_options, serial_kernel_option = get_serial_options(machine)
        options += serial_options
        kernel_options += serial_kernel_option
    options += """ --kernel-options="{options}" """.format(options=kernel_options)
    return options


def get_bmc_command(machine, cobbler_path):
    if not hasattr(machine, 'bmc') or not machine.bmc:
        logger.error("Tried to get bmc command for %s, which does not have one", machine.fqdn)
    bmc = machine.bmc
    bmc_command = """{cobbler} system edit --name={name} --interface=bmc --interface-type=bmc"""\
        .format(cobbler=cobbler_path, name=machine.fqdn)
    bmc_command += """ --ip-address="{ip}" --mac="{mac}" --dns-name="{dns}" --ipv6-address="{ipv6}" """.format(
        ip=get_ipv4(bmc.fqdn) or '',
        mac=bmc.mac or '',
        dns=get_hostname(bmc.fqdn) or '',
        ipv6=get_ipv6(bmc.fqdn) or '')
    return bmc_command


def get_power_options(machine):
    if not machine.remotepower:
        logger.error("machine %s has no remotepower", machine.fqdn)
        raise ValueError("machine {0} has no remotepower".format(machine.fqdn))
    remotepower = machine.remotepower
    fence = RemotePowerType.from_fence(remotepower.fence_name)
    options = " --power-type={} ".format(fence.fence)

    if fence.use_identity_file:
        options += " --power-user={user} --power-identity-file={key}".format(
            user=fence.username, key=fence.identity_file)
    else:
        username, password = remotepower.get_credentials()
        options += " --power-user={username} --power-pass={password} ".format(username=username,
                                                                              password=password)
    if fence.use_hostname_as_port:
        options += " --power-id={port}".format(port=get_hostname(machine.hostname))
    elif fence.use_port:
        # Temporary workaround until fence raritan accepts port as --plug param
        if fence.fence == "raritan":
            options += " --power-id=system1/outlet{port}".format(port=remotepower.port)
        options += " --power-id={port}".format(port=remotepower.port)

    options += " --power-address={address}".format(address=remotepower.get_power_address())
    if fence.use_options:
        options += " --power-options={options}".format(options=remotepower.options)
    return options


def get_serial_options(machine):
    console = machine.serialconsole
    options = """ --serial-device="{device}" """.format(device=console.kernel_device_num)
    options += """--serial-baud-rate="{baud}" """.format(baud=console.baud_rate)
    kernel_option = ""
    if console.kernel_device != "None":
        kernel_option += " console={device}{num},{baud} ".format(device=console.kernel_device,
                                                                 num=console.kernel_device_num,
                                                                 baud=console.baud_rate)
    return (options, kernel_option)


def get_cobbler_add_command(machine, cobber_path):
    profile = get_default_profile(machine)
    if not profile:
        raise CobblerException("could not determine default profile for machine {machine}".format(
                               machine=machine.fqdn))
    command = "{cobbler} system add {options} --netboot-enabled=False --profile={profile}".format(
        cobbler=cobber_path, options=create_cobbler_options(machine), profile=profile)
    return command


def get_cobbler_update_command(machine, cobber_path):
    command = "{cobbler} system edit {options}".format(cobbler=cobber_path,
                                                       options=create_cobbler_options(machine))
    return command


def get_filename(machine):
    """
    Return the corresponding filename attribute for the DHCP record.

    Machine > Group > Architecture > None
    """
    context = Context({'machine': machine})

    if machine.dhcp_filename:
        filename = machine.dhcp_filename
    elif machine.group and machine.group.dhcp_filename:
        filename = Template(machine.group.dhcp_filename).render(context)
    elif machine.architecture.dhcp_filename:
        filename = Template(machine.architecture.dhcp_filename).render(context)
    else:
        filename = None

    return filename


class CobblerServer:

    def __init__(self, fqdn, domain):
        self._fqdn = fqdn
        self._conn = None
        self._domain = domain
        self._cobbler_path = ServerConfig.objects.by_key("cobbler.command")

    @staticmethod
    def from_machine(machine: Machine):
        """
        Return the cobbler server associated to a machine

        :param machine: Machine object which is managed by the cobbler server to fetch
        :returns: The corresponding cobbler server or None
        """
        domain = machine.fqdn_domain
        server = domain.cobbler_server
        if server:
            return CobblerServer(server.fqdn, domain)
        return None

    def connect(self):
        """Connect to DHCP server via SSH."""
        if not self._conn:
            self._conn = SSH(self._fqdn)
            self._conn.connect()

    def close(self):
        """Close connection to DHCP server."""
        if self._conn:
            self._conn.close()

    def deploy(self):
        self.connect()
        if not self.is_installed():
            raise CobblerException("No Cobbler service found: {}".format(self._fqdn))
        if not self.is_running():
            raise CobblerException("Cobbler server is not running: {}".format(self._fqdn))
        machines = Machine.active_machines.filter(fqdn_domain=self._domain.pk)
        cobbler_machines = self.get_machines()
        cobbler_commands = []
        for machine in machines:
            if machine.fqdn in cobbler_machines:
                cobbler_commands.append(get_cobbler_update_command(machine, self._cobbler_path))
            else:
                cobbler_commands.append(get_cobbler_add_command(machine, self._cobbler_path))
            if hasattr(machine, 'bmc') and machine.bmc:
                cobbler_commands.append(get_bmc_command(machine, self._cobbler_path))

        logger.info("=======================")
        logger.info(machines)
        logger.info(cobbler_machines)
        logger.info(cobbler_commands)
        logger.info("=======================")

        for command in cobbler_commands:  # TODO: Convert this to a single ssh call (performance)
            logger.debug("executing %s ", command)
            stdout, stderr, exitcode = self._conn.execute(command)
            if exitcode:
                logger.error("failed to execute %s on %s with error '%s' and stdout '%s'",
                             command, self._fqdn, stderr, stdout)

        self.close()

    def update_or_add(self, machine: Machine):
        self.connect()
        self._check()
        if machine.fqdn in self.get_machines():
            command = get_cobbler_update_command(machine, self._cobbler_path)
        else:
            command = get_cobbler_add_command(machine, self._cobbler_path)
        logger.debug("Executing Cobbler command %s", command)
        stdout, stderr, exitcode = self._conn.execute(command)
        if exitcode:
            logger.error(
                "Update or Add with command \n '%s'\n failed, giving \n '%s',\nand stdout '%s'", command, stderr, stdout
            )
        self._conn.execute(command)
        if hasattr(machine, 'bmc') and machine.bmc:
            command = get_bmc_command(machine, self._cobbler_path)
            logger.debug("Executing Cobbler command %s", command)
            stdout, stderr, exitcode = self._conn.execute(command)
            if exitcode:
                logger.error(
                    "writing BMC data to cobbler with \n'%s' failed, giving \n '%s',\nand stdout '%s'",
                    command, stderr, stdout
                )

    def remove(self, machine: Machine):
        self.connect()
        if not self.is_installed():
            raise CobblerException("No Cobbler service found: {}".format(self._fqdn))
        if not self.is_running():
            raise CobblerException("Cobbler server is not running: {}".format(self._fqdn))
        command = "{cobbler} system remove --name {fqdn}".format(
            cobbler=self._cobbler_path, fqdn=machine.fqdn)
        stdout, stderr, exitcode = self._conn.execute(command)
        if exitcode:
            logging.error("Removing %s failed with '%s' and stdout '%s'",
                          machine.fqdn, stderr, stdout)

    def sync_dhcp(self):
        self.connect()
        self._check()
        stdout, stderr, exitcode = self._conn.execute(
            "{cobbler} sync --dhcp".format(cobbler=self._cobbler_path))
        if exitcode:
            logging.error("Dhcp sync on %s failed with '%s' and stdout '%s'",
                          self._fqdn, stderr, stdout)

    def is_installed(self):
        """Check if Cobbler server is available."""
        if self._conn.check_path(self._cobbler_path, '-x'):
            return True
        return False

    def is_running(self):
        """Check if the Cobbler daemon is running via the cobbler version command."""
        command = "{} version".format(self._cobbler_path)
        _, _, exitstatus = self._conn.execute(command)
        if exitstatus == 0:
            return True
        return False

    def get_machines(self):
        stdout, stderr, exitstatus = self._conn.execute(
            "{cobbler} system list".format(cobbler=self._cobbler_path))
        if exitstatus:
            logger.warning("system list failed on %s with %s", self._fqdn, stderr)
            raise CobblerException("system list failed on {server}".format(server=self._fqdn))
        clean_out = [system.strip(' \n\t') for system in stdout]
        return clean_out

    def setup(self, machine: Machine, choice: str):
        logger.info("setup called for %s with %s on cobbler server %s ",
                    machine.fqdn, self._fqdn, choice)
        if choice:
            cobbler_profile = " --profile={arch}:{profile}".format(
                arch=machine.architecture, profile=choice)
        else:
            cobbler_profile = ""

        command = "{cobbler} system edit --name={machine} {profile}  --netboot=True".format(
            cobbler=self._cobbler_path,
            machine=machine.fqdn,
            profile=cobbler_profile)
        logger.debug("command for setup: %s", command)
        self.connect()
        try:
            _stdout, stderr, exitstatus = self._conn.execute(command)
            if exitstatus:
                logger.warning("setup of  %s with %s failed on %s with %s", machine.fqdn,
                               cobbler_profile, self._fqdn, stderr)
                raise CobblerException(
                    "setup of {machine} with {profile} failed on {server} with {error}".format(
                        machine=machine.fqdn, profile=cobbler_profile, server=self._fqdn, error=stderr))
        except Exception:
            pass
        finally:
            self.close()

    def powerswitch(self, machine: Machine, action: str):
        logger.debug("powerswitching of %s called with action %s", machine.fqdn, action)
        self.connect()
        cobbler_action = ""
        if action == "reboot":
            cobbler_action = "reboot"
        else:
            cobbler_action = "power" + action

        command = "{cobbler} system {action} --name  {fqdn}".format(cobbler=self._cobbler_path,
                                                                    action=cobbler_action,
                                                                    fqdn=machine.fqdn)
        out, stderr, exitcode = self._conn.execute(command)
        logger.debug("powerswitching of %s called with action %s", machine.fqdn, action)
        logger.debug("Execute on cobbler: %s", command)
        if exitcode:
            logger.warning("Powerswitching of  %s with %s failed on %s with %s", machine.fqdn,
                           command, self._fqdn, stderr)
            raise CobblerException(
                "Powerswitching of {machine} with {command} failed on {server} with {error}".format(
                    machine=machine.fqdn, command=command, server=self._fqdn, error=stderr))
        return out

    def _check(self):
        if not self.is_installed():
            raise CobblerException("No Cobbler service found: {}".format(self._fqdn))
        if not self.is_running():
            raise CobblerException("Cobbler server is not running: {}".format(self._fqdn))
