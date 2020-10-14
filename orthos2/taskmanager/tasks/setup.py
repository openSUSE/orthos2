import logging

from data.models import Machine, ServerConfig
from django.template import Context, Template
from taskmanager.models import Task
from utils.ssh import SSH

logger = logging.getLogger('tasks')


class SetupMachine(Task):
    """Setup machine."""

    def __init__(self, fqdn, choice=None):
        self.fqdn = fqdn
        if choice:
            self.choice = choice
        else:
            self.choice = 'default'

    def execute(self):
        """Execute the task."""
        if not ServerConfig.objects.bool_by_key('orthos.debug.setup.execute'):
            logger.warning("Disabled: set 'orthos.debug.setup.execute' to 'true'")
            return

        logger.debug('Calling setup script...')

        try:
            machine = Machine.objects.get(fqdn=self.fqdn)
            tftp_server = machine.fqdn_domain.tftp_server

            if not tftp_server:
                logger.warning(
                    "No TFTP server available for '{}'".format(machine.fqdn_domain.name)
                )
                return

            command_template = ServerConfig.objects.by_key('setup.execute.command')

            context = Context({
                'machine': machine,
                'choice': self.choice
            })

            command = Template(command_template).render(context)

            logger.debug("Initialize setup {}@{}: {}:{}".format(
                self.choice,
                machine.fqdn,
                tftp_server.fqdn,
                command
            ))

            tftp_server = SSH(tftp_server.fqdn)
            tftp_server.connect()
            stdout, stderr, exitstatus = tftp_server.execute(command)
            tftp_server.close()

            if exitstatus != 0:
                logger.warning("Creating setup configuration failed for '{}'".format(machine))
                return

            # reboot machine finally
            machine.reboot()

        except SSH.Exception as exception:
            logger.error(exception)
        except Machine.DoesNotExist:
            logger.error("Machine does not exist: fqdn={}".format(self.fqdn))
        except Exception as e:
            logger.exception(e)
