import logging
from typing import TYPE_CHECKING, Tuple

from django.db import models
from django.db.models import QuerySet
from requests import HTTPError

from orthos2.data.models.platform import Platform
from orthos2.utils.netbox import Netbox

if TYPE_CHECKING:
    from orthos2.data.models.machine import Machine
    from orthos2.types import OptionalPlatformForeignKey

logger = logging.getLogger("models")


class Enclosure(models.Model):
    name: "models.CharField[str, str]" = models.CharField(
        max_length=200,
        blank=False,
        unique=True,
    )

    platform: "OptionalPlatformForeignKey" = models.ForeignKey(
        Platform,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        limit_choices_to={"is_cartridge": False},
    )

    description: "models.CharField[str, str]" = models.CharField(
        max_length=512,
        blank=True,
    )

    machine_set: models.Manager["Machine"]

    netbox_id: "models.PositiveIntegerField[int, int]" = models.PositiveIntegerField(
        verbose_name="NetBox ID",
        help_text="The ID that NetBox gives to the object.",
        default=0,
    )

    location_site: "models.CharField[str, str]" = models.CharField(
        max_length=512,
        default="unknown",
    )

    location_room: "models.CharField[str, str]" = models.CharField(
        max_length=512,
        default="unknown",
    )

    location_rack: "models.CharField[str, str]" = models.CharField(
        max_length=512,
        default="unknown",
    )

    location_rack_position: "models.CharField[str, str]" = models.CharField(
        max_length=512,
        default="unknown",
    )

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
        Return all non-virtual machines (systems) of the enclosure.

        The following systems are excluded:
            RemotePower,
            BMC
        """
        machines = self.get_machines().filter(system__virtual=False)
        return machines

    def fetch_netbox(self) -> None:
        """
        Fetch all information about a machine from NetBox if the NetBox ID is set.
        """
        if self.netbox_id == 0:
            logger.debug("Skipping fetching from NetBox because NetBox ID is 0.")
            return
        netbox_api = Netbox.get_instance()
        try:
            netbox_device = netbox_api.fetch_device(self.netbox_id)
        except HTTPError as e:
            if e.response.status_code == 404:
                logger.info("Fetching from NetBox failed with status 404.")
                return
            raise e
        # Reset fields
        self.comment = ""
        self.location_site = "unknown"
        self.location_room = "unknown"
        self.location_rack = "unknown"
        self.location_rack_position = "unknown"
        # Description
        self.comment = netbox_device.get("description", "")
        # Location
        self.location_site = netbox_device.get("site", {}).get("display", "unknown")
        location_obj = netbox_device.get("location", {})
        self.location_room = location_obj.get("display", "unknown")
        rack_obj = netbox_device.get("rack", {})
        self.location_rack = rack_obj.get("display", "unknown")
        # TODO: What if the position is not set.
        self.location_rack_position = netbox_device.get("position", "unknown")
        self.save()
