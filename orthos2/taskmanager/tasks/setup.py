import logging

from orthos2.data.models import Machine, ServerConfig
from orthos2.taskmanager.models import Task
from orthos2.utils.cobbler import CobblerException, CobblerServer
from orthos2.utils.ssh import SSH

logger = logging.getLogger('tasks')


class SetupMachine(Task):
    """Setup machine."""

    def __init__(self, fqdn, choice=None):
        self.fqdn = fqdn
        self.choice = choice

    def execute(self):
        """Execute the task."""
        if not ServerConfig.objects.bool_by_key('orthos.debug.setup.execute'):
            logger.warning("Disabled: set 'orthos.debug.setup.execute' to 'true'")
            return

        logger.debug('Executing setup')

        try:
            machine = Machine.objects.get(fqdn=self.fqdn)
            domain = machine.fqdn_domain
            servers = domain.cobbler_server.all()
            if not servers:
                logger.warning("No cobbler server available for '%s'", machine.fqdn_domain.name)
                return

            for server in servers:
                try:
                    logger.debug("trying %s for setup", server.fqdn)
                    cobbler_server = CobblerServer(server.fqdn, domain)
                    cobbler_server.setup(machine, self.choice)

                except CobblerException as e:
                    logger.warning("Setup of %s with %s failed on %s with %s", machine.fqdn,
                                   self.choice, server.fqdn, e)
                else:
                    logger.debug("success")
                    machine.reboot()
                    break
            else:
                logger.exception("Setup of %s with %s failed on all cobbler servers",
                                 machine.fqdn, self.choice)

        except SSH.Exception as exception:
            logger.exception(exception)
        except Machine.DoesNotExist:
            logger.exception("Machine does not exist: fqdn=%s", self.fqdn)
        except Exception as e:
            logger.exception(e)
