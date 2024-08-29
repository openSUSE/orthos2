import logging
from typing import Optional

from orthos2.data.models import Machine, ServerConfig
from orthos2.taskmanager.models import Task
from orthos2.utils.cobbler import CobblerException, CobblerServer
from orthos2.utils.ssh import SSH

logger = logging.getLogger("tasks")


class SetupMachine(Task):
    """Setup machine."""

    def __init__(self, fqdn: str, choice: Optional[str] = None) -> None:
        self.fqdn = fqdn
        self.choice = choice

    def execute(self) -> None:
        """Execute the task."""
        if not ServerConfig.objects.bool_by_key("orthos.debug.setup.execute"):
            logger.warning("Disabled: set 'orthos.debug.setup.execute' to 'true'")
            return

        logger.debug("Executing setup")

        try:
            machine = Machine.objects.get(fqdn=self.fqdn)
            domain = machine.fqdn_domain
            server = domain.cobbler_server
            if not server:
                logger.warning(
                    "No cobbler server available for '%s'", machine.fqdn_domain.name
                )
                return

            try:
                logger.debug("trying %s for setup", server.fqdn)
                cobbler_server = CobblerServer(server.fqdn, domain)  # type: ignore
                cobbler_server.setup(machine, self.choice)  # type: ignore

            except CobblerException as e:
                logger.warning(
                    "Setup of %s with %s failed on %s with %s",
                    machine.fqdn,
                    self.choice,
                    server.fqdn,
                    e,
                )
            else:
                logger.debug("success")
                machine.reboot()

        except SSH.Exception as exception:
            logger.exception(exception)
        except Machine.DoesNotExist:
            logger.exception("Machine does not exist: fqdn=%s", self.fqdn)
        except Exception as e:
            logger.exception(e)
