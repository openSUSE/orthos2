import logging
import socket
from typing import Dict, List, Optional, Tuple

from django.conf import settings

from orthos2.data.models import Machine

logger = logging.getLogger("utils")


class HostnameFinder(object):
    """
    Find an unused hostname. Obtail a hostname finder with::

        finder = HostnameFinder.by_domain(domain)

    and find a new hostname with::

        hostnames = finder.free_hostnames()
        if len(hostnames) > 0:
            free_hostname = hostnames[0]

    """

    @staticmethod
    def by_domain(domain: str, arch: str = "x86_64"):
        """
        Returns a HostnameFinder instance by domain.
        """
        if not hasattr(settings, "HOSTNAMEFINDER"):
            logger.info("Config file is missing HOSTNAMEFINDER variable")
            return None
        config = next(
            (x for x in settings.HOSTNAMEFINDER if x["network"] == domain), None
        )
        if not config:
            logger.info("Domain %s has no hostfinder configuration", domain)
            return None
        return HostnameFinder(config)

    def __init__(self, config: Dict[str, str]):
        """
        Creates a new object with the given domain model object.
        """
        self.domain = config["network"]
        self.arch = config["arch"]
        self.sections = config["section"]
        if not hasattr(config, "ip_range"):
            self.ip_range = range(1, 254)
        else:
            self.ip_range = config["ip_range"]

    def free_hostnames(self) -> Tuple[List[str], List[str]]:
        """
        Returns the free hostnames in the 10.161.<section>.<ip_range> area.
        """

        used: List[str] = []
        unused: List[str] = []
        # get the hostnames in the database
        Machines = set(
            Machine.objects.filter(fqdn_domain__name=self.domain).values_list(
                "fqdn", flat=True
            )
        )
        for i in self.sections:
            for j in self.ip_range:
                ip = "10.161.%d.%d" % (i, j)
                try:
                    res = socket.gethostbyaddr(ip)
                except socket.error:
                    continue
                name = res[0]
                if name in Machines:
                    used.append(name)
                    continue
                unused.append(name)
        return used, unused

    def get_hostname(self) -> Optional[List[str]]:
        hostnames = self.free_hostnames()
        if len(hostnames) < 1:
            return None
        # return hostnames[random.randint(0, len(hostnames))]
        return hostnames[0]
