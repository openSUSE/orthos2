import datetime
import logging
import uuid
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple

from django.db import models
from django.db.models import QuerySet
from django.utils import timezone
from requests import HTTPError

from orthos2.data.models.netboxorthoscomparision import (
    NetboxOrthosComparisionResult,
    NetboxOrthosComparisionRun,
)
from orthos2.data.models.platform import Platform
from orthos2.utils.netbox import Netbox

if TYPE_CHECKING:
    from django.db.models.fields.related_descriptors import RelatedManager

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

    netboxorthoscomparisionruns: "RelatedManager[NetboxOrthosComparisionRun]"

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

    def fetch_netbox_record(self) -> Optional[Dict[str, Any]]:
        """
        Fetch the record of this Machine object. This will attempt to search either the DCIM or Virtual Machine
        endpoint of NetBox, depending on the System type of the machine.

        :returns: None in case the record cannot be retrieved. The Dict with the NetBox data otherwhise.
        :raises HTTPError: In case any HTTP code except 200 and 404 is returned.
        """
        netbox_api = Netbox.get_instance()
        # Take any machine as they should be of the system system type
        machine = self.machine_set.first()
        if machine is None:
            logger.info("Cannot fetch record for enclosure without machines.")
            return None
        if machine.system.virtual:
            try:
                netbox_machine = netbox_api.fetch_vm(self.netbox_id)
            except HTTPError as e:
                if e.response.status_code == 404:
                    logger.info("Fetching VM from NetBox failed with status 404.")
                    return None
                raise e
        else:
            try:
                netbox_machine = netbox_api.fetch_device(self.netbox_id)
            except HTTPError as e:
                if e.response.status_code == 404:
                    logger.info("Fetching Device from NetBox failed with status 404.")
                    return None
                raise e
        return netbox_machine

    def compare_netbox(self) -> None:
        """
        Compare the current data in the database of Orthos 2 with the data from NetBox.
        """
        if self.netbox_id == 0:
            logger.debug("Skipping comparision because NetBox ID is 0.")
            return

        run_uuid = uuid.uuid4()
        run_obj = NetboxOrthosComparisionRun(
            run_id=run_uuid,
            compare_timestamp=datetime.datetime.now(tz=timezone.get_current_timezone()),
            object_type=NetboxOrthosComparisionRun.NetboxOrthosComparisionItemTypes.ENCLOSURE,
            object_enclosure=self,
        )
        run_obj.save()

        netbox_device = self.fetch_netbox_record()
        if netbox_device is None:
            return

        # Description
        NetboxOrthosComparisionResult(
            run_id=run_obj,
            property_name="description",
            orthos_result=self.description or "None",
            netbox_result=netbox_device.get("description", "None"),
        ).save()
        # Location Site
        NetboxOrthosComparisionResult(
            run_id=run_obj,
            property_name="location_site",
            orthos_result=self.location_site or "None",
            netbox_result=netbox_device.get("site", {}).get("display", "None"),
        ).save()
        location_obj = netbox_device.get("location")
        # Location Room
        if location_obj is None:
            netbox_location_room_result = "unknown"
        else:
            netbox_location_room_result = location_obj.get("display", "None")
        NetboxOrthosComparisionResult(
            run_id=run_obj,
            property_name="location_room",
            orthos_result=self.location_room or "None",
            netbox_result=netbox_location_room_result,
        ).save()
        rack_obj = netbox_device.get("rack")
        # Location Rack
        NetboxOrthosComparisionResult(
            run_id=run_obj,
            property_name="location_rack",
            orthos_result=self.location_rack or "None",
            netbox_result=(
                "unknown" if rack_obj is None else rack_obj.get("display", "None")
            ),
        ).save()
        # Location Rack Position
        # TODO: What if the position is not set.
        netbox_location_rack_position_result = netbox_device.get("position", "None")
        if netbox_location_rack_position_result is None:
            # In case the location is unset in NetBox, the result is "None" due to the JSON value being "null".
            netbox_location_rack_position_result = "unknown"
        NetboxOrthosComparisionResult(
            run_id=run_obj,
            property_name="location_rack_position",
            orthos_result=self.location_rack_position or "None",
            netbox_result=netbox_location_rack_position_result,
        ).save()

    def fetch_netbox(self) -> None:
        """
        Fetch all information about a machine from NetBox if the NetBox ID is set.
        """
        if self.netbox_id == 0:
            logger.debug("Skipping fetching from NetBox because NetBox ID is 0.")
            return

        netbox_device = self.fetch_netbox_record()
        if netbox_device is None:
            return

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
