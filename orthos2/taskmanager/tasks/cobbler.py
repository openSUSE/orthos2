import logging

from django.conf import settings

from orthos2.data.models import Domain, Machine, ServerConfig
from orthos2.taskmanager.models import Task
from orthos2.utils.cobbler import CobblerServer
from orthos2.utils.ssh import SSH

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
        if self._domain_id:
            return Domain.objects.filter(pk=self._domain_id)
        else:
            return Domain.objects.all()

    def execute(self):
        """
        Executes the task.
        """

        if settings.DEBUG and not ServerConfig.objects.bool_by_key('orthos.debug.dhcp.write'):
            logger.warning("Disabled: set 'orthos.debug.dhcp.write' to 'true'")
            return

        try:
            domains = self._get_domains()
            logger.info("--- Start Cobbler deployment ---")
            for domain in domains:

                if domain.cobbler_server.all().count() == 0:
                    logger.info("Domain '%s' has no Cobbler server... skip", domain.name)
                    continue

                if domain.machine_set.count() == 0:
                    logger.info("Domain '%s' has no machines... skip", domain.name)
                    continue

                logger.info("Generate Cobbler configuration for '%s'...", domain.name)

                # deploy generated DHCP files on all servers belonging to one domain
                for server in domain.cobbler_server.all():

                    cobbler_server = CobblerServer(server.fqdn, domain)
                    try:
                        logger.info("* Cobbler deployment started...")
                        cobbler_server.deploy()
                        logger.info("* Cobbler deployment finished successfully")
                    except Exception as e:
                        message = "* Cobbler deployment failed; {}".format(e)
                        if isinstance(e, (SystemError, SyntaxError)):
                            logger.exception(message)
                        else:
                            logger.exception(message)

        except SSH.Exception as e:
            logger.exception(e)
        except Exception as e:
            logger.exception(e)
        finally:
            logger.info("--- Cobbler deployment finished ---")

class UpdateCobblerMachine(Task):
    def __init__(self, domain_id, machine_id):
        self._domain_id = domain_id
        self._machine_id = machine_id
    def execute(self):
        try:
            domain = Domain.objects.get(pk=self._domain_id)
            machine = Machine.objects.get(pk=self._machine_id)
            logger.info("Cobbler update started")
            if domain.cobbler_server.all().count() == 0:
                    logger.info("Domain '%s' has no Cobbler server... aborting", domain.name)
                    return
            logger.info("Generate Cobbler update configuration for '%s'...", machine.fqdn)
            # deploy generated DHCP files on all servers belonging to one domain
            for server in domain.cobbler_server.all():
                cobbler_server = CobblerServer(server.fqdn, domain)
                try:
                    logger.info("* Cobbler deployment started...")
                    cobbler_server.update_or_add(machine)
                    logger.info("* Cobbler deployment finished successfully")
                except Exception as e:
                    message = "* Cobbler deployment failed; {}".format(e)
                    if isinstance(e, (SystemError, SyntaxError)):
                        logger.exception(message)
                    else:
                        logger.exception(message)
        except SSH.Exception as e:
            logger.exception(e)
        except Domain.DoesNotExist:
            logger.error("No Domain with id %s, aborting", self._domain_id)
        except Domain.MultipleObjectsReturned:
            logger.error("Multiple Domains with id %s, aborting", self._domain_id)
        except Machine.DoesNotExist:
            logger.error("No Machine with id %s, aborting", self._machine_id)
        except Machine.MultipleObjectsReturned:
            logger.error("Multiple Machines with id %s, aborting", self._machine_id)
            return
        except Exception as e:
            logger.exception(e)
        finally:
            logger.info("--- Cobbler deployment finished ---")


class SyncCobblerDHCP(Task):
    def __init__(self, domain_id):
        self._domain_id = domain_id

    def execute(self):
        try:
            domain = Domain.objects.get(pk=self._domain_id)
            if domain.cobbler_server.all().count() == 0:
                    logger.info("Domain '%s' has no Cobbler server... aborting", domain.name)
                    return
            for server in domain.cobbler_server.all():
                server.sync_dhcp()
        except Domain.DoesNotExist:
            logger.error("No Domain with id %s, aborting", self._domain_id)
        except Domain.MultipleObjectsReturned:
            logger.error("Multiple Domains with id %s, aborting", self._domain_id)