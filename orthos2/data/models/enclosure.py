import json
import logging
import ssl
import urllib.request
from typing import TYPE_CHECKING, Optional, Tuple

from django.db import models
from django.db.models import QuerySet
from django.template import Context, Template

from .platform import Platform
from .serverconfig import ServerConfig

if TYPE_CHECKING:
    from orthos2.data.models.machine import Machine

logger = logging.getLogger("models")


class Enclosure(models.Model):
    name = models.CharField(max_length=200, blank=False, unique=True)

    platform = models.ForeignKey(
        Platform,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        limit_choices_to={"is_cartridge": False},
    )

    description = models.CharField(max_length=512, blank=True)

    machine_set: models.Manager["Machine"]

    location_room = "unknown"

    location_rack = "unknown"

    location_rack_position = "unknown"

    def natural_key(self) -> Tuple[str]:
        return (self.name,)

    def __str__(self) -> str:
        return self.name

    def get_machines(self) -> QuerySet["Machine"]:
        return self.machine_set.all()

    def get_virtual_machines(self) -> QuerySet["Machine"]:
        """Return all virtual machines (systems) of the enclosure."""
        return self.get_machines().filter(system__virtual=True)

    def get_non_virtual_machines(self) -> QuerySet["Machine"]:
        """
        Return all non virtual machines (systems) of the enclosure.

        The following systems are excluded:
            RemotePower,
            BMC
        """
        machines = self.get_machines().filter(system__virtual=False)
        return machines

    def fetch_location(self, pk: Optional[int] = None) -> None:
        """
        Fetch location from RackTables.

        If `pk` is set, use this ID to query API. Otherwise, try the first machine ID belonging to
        this enclosure.
        """
        try:
            if pk is None:
                pk = self.machine_set.first().pk  # type: ignore

            template = ServerConfig.objects.by_key("racktables.url.query")

            context = Context({"id": pk})

            url = Template(template).render(context)  # type: ignore

            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            with urllib.request.urlopen(url, context=ssl_context) as result:
                data = json.loads(result.read().decode())

                if data is None:
                    return

                room = data[str(pk)]["Location"]
                rack = data[str(pk)]["Rackname"]
                rack_position = data[str(pk)]["Position"]

                self.location_room = room
                self.location_rack = rack
                self.location_rack_position = rack_position

        except Exception as e:
            logger.warning(
                "Couldn't fetch location information for enclosure '%s': %s", self, e
            )
