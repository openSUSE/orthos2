import logging

from orthos2.data.models import Machine, ServerConfig
from django.template import Context, Template
from orthos2.utils.ssh import SSH

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

from orthos2.utils.misc import get_ip
def create_cobbler_options(machine):
    tftp_server = get_tftp_server(machine)
    options = " --name={name} --ip-address={ipv4}".format(name=machine.fqdn, ipv4=machine.ipv4)
    if machine.ipv6:
        options += " --ipv6-address={ipv6}".format(ipv6=machine.ipv6)
    options += " --interface=default --management=True --interface-master=True"
    if get_filename(machine):
        options += " --filename={filename}".format(filename=get_filename(machine))
    if tftp_server:
        ipv4 = get_ip(tftp_server)
        if ipv4:
            options += " --next-server={server}".format(server=ipv4[0])
    return options


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
        for command in cobbler_commands:  # TODO: Convert this to a single ssh call (performance)
            _, stderr, exitcode = self._conn.execute(command)
            if exitcode:
                logger.error("failed to execute %s on %s with error %s",
                             command, self._fqdn, stderr)

        self.close()

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

    @staticmethod
    def profile_normalize(string):
        '''
        This method replaces the second colon (:) of a string with a dash (-)
        This is to convert:
        x86_64:SLE-12-SP4-Server-LATEST:install
        to
        x86_64:SLE-12-SP4-Server-LATEST-install
        until cobbler returns profiles where arch:distro:profile are all separated via :
        '''
        return string.replace(':', '-', 2).replace('-', ':', 1)

    def setup(self, machine: Machine, choice: str):
        logger.info("setup called for %s with %s on cobbler server %s ", machine.fqdn, self._fqdn,
            choice)
        cobbler_profile = "{arch}:{profile}".format(arch=machine.architecture, profile=choice)

        # ToDo: Revert this after renaming cobbler profiles
        cobbler_profile = CobblerServer.profile_normalize(cobbler_profile)

        command = "{cobbler} system edit --name={machine}  --profile={profile} --netboot=True"\
            .format(cobbler=self._cobbler_path, machine=machine.fqdn, profile=cobbler_profile)
        logger.debug("command for setup: %s", command)
        self.connect()
        try:
            stdout, stderr, exitstatus = self._conn.execute(command)
            if exitstatus:
                logger.warning("setup of  %s with %s failed on %s with %s", machine.fqdn, 
                               cobbler_profile, self._fqdn, stderr)
                raise CobblerException(
                    "setup of {machine} with {profile} failed on {server} with {error}".format(
                        machine=machine.fqdn, arch=cobbler_profile, server=self._fqdn))
        except:
            pass
        finally:
            self.close()
