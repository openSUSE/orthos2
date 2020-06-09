import json
import logging
import ssl
import urllib.request

from django.conf import settings
from django.db import models
from django.template import Context, Template

from .platform import Platform
from .serverconfig import ServerConfig
from .system import System

logger = logging.getLogger('models')


class Enclosure(models.Model):
    name = models.CharField(max_length=200, blank=False, unique=True)

    platform = models.ForeignKey(
        Platform,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        limit_choices_to={'is_cartridge': False}
    )

    description = models.CharField(
        max_length=512,
        blank=True
    )

    location_room = 'unknown'

    location_rack = 'unknown'

    location_rack_position = 'unknown'

    updated = models.DateTimeField(
        'Updated at',
        auto_now=True
    )

    created = models.DateTimeField(
        'Created at',
        auto_now_add=True
    )

    def __str__(self):
        return self.name

    def get_machines(self):
        return self.machine_set.all()

    def get_virtual_machines(self):
        """
        Returns all virtual machines (systems) of the enclosure.
        """
        return self.get_machines().filter(system__virtual=True)

    def get_non_virtual_machines(self):
        """
        Returns all non virtual machines (systems) of the enclosure. The following systems are
        excluded:

            RemotePower,
            BMC
        """
        machines = self.get_machines().filter(system__virtual=False)
        machines = machines.exclude(system=System.Type.REMOTEPOWER)
        machines = machines.exclude(system=System.Type.BMC)
        return machines

    def get_bmc_list(self):
        """
        Returns all baseboard management controller (BMC) of the enclosure.
        """
        return self.get_machines().filter(system=System.Type.BMC)

    def fetch_location(self, pk=None):
        """
        Fetch location from RackTables. If `pk` is set, use this ID to query API. Otherwise try
        the first machine ID belonging to this enclosure.
        """
        try:
            if pk is None:
                pk = self.machine_set.first().pk

            template = ServerConfig.objects.by_key('racktables.url.query')

            context = Context({
                'id': pk
            })

            url = Template(template).render(context)

            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            with urllib.request.urlopen(url, context=ssl_context) as result:
                data = json.loads(result.read().decode())

                if data is None:
                    return

                room = data[str(pk)]['Location']
                rack = data[str(pk)]['Rackname']
                rack_position = data[str(pk)]['Position']

                self.location_room = room
                self.location_rack = rack
                self.location_rack_position = rack_position

        except Exception as e:
            logger.warning(
                "Couldn't fetch location information for enclosure '{}': {}".format(self, e)
            )
