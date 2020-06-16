import collections
import logging
import os

from data.models import Domain, Machine, ServerConfig
from taskmanager.models import Task
from utils.cobbler import CobblerServer
from utils.ssh import SSH

logger = logging.getLogger('tasks')


class RegenerateCobbler(Task):
    """
    Regenerates the Cobbler configurations for IPv4/IPv6.
    """

    def __init__(self, domain_id=None):
        self._domain_id = domain_id

    def _get_domains(self):
        """
        Returns network domain(s) for which Cobbler entries should be regenerated. Return all if no
        domain ID is given.
        """
        if not self._domain_id:
            return Domain.objects.all()
        else:
            return Domain.objects.filter(pk=self._domain_id)

    def execute(self):
        """
        Executes the task.
        """

        if not ServerConfig.objects.bool_by_key('orthos.debug.dhcp.write'):
            logger.warning("Disabled: set 'orthos.debug.dhcp.write' to 'true'")
            return

        try:
            domains = self._get_domains()
            logger.info("--- Start Cobbler deployment ---")
            for domain in domains:

                if domain.cobbler_server.all().count() == 0:
                    logger.info("Domain '{}' has no Cobbler server... skip".format(domain.name))
                    continue

                if domain.machine_set.count() == 0:
                    logger.info("Domain '{}' has no machines... skip".format(domain.name))
                    continue

                logger.info("Generate Cobbler configuration for '{}'...".format(domain.name))

                # deploy generated DHCP files on all servers belonging to one domain
                for server in domain.cobbler_server.all():

                    cobbler_server = CobblerServer(server.fqdn, domain)
                    try:
                        logger.info("* Cobbler deployment started...")
                        cobbler_server.deploy()
                        logger.info("* Cobbler deployment finished successfully")
                    except Exception as e:
                        message = "* Cobbler deployment failed; {}".format(e)
                        if type(e) in (SystemError, SyntaxError):
                            logger.error(message)
                        else:
                            logger.exception(message)

        except SSH.Exception as e:
            logger.error(e)
        except Exception as e:
            logger.exception(e)
        finally:
            logger.info("--- Cobbler deployment finished ---")
