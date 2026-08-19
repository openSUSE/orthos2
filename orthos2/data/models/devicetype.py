import datetime
import logging
import uuid
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple, Union, cast

from django.contrib import admin
from django.db import models
from django.utils import timezone
from requests import HTTPError

from orthos2.data.models.manufacturer import Manufacturer
from orthos2.data.models.netboxorthoscomparision import (
    NetboxOrthosComparisionResult,
    NetboxOrthosComparisionRun,
)
from orthos2.utils.netbox import Netbox

if TYPE_CHECKING:
    from django.db.models.expressions import Combinable

    from orthos2.data.models.enclosure import Enclosure
    from orthos2.types import OptionalDateTimeField

logger = logging.getLogger("models")


class DeviceTypeManager(models.Manager["DeviceType"]):
    def get_by_natural_key(self, name: str) -> "DeviceType":
        return self.get(name=name)


class DeviceType(models.Model):
    class Meta:  # type: ignore
        ordering = ["manufacturer", "name"]

    id: int

    name: "models.CharField[str, str]" = models.CharField(max_length=200, blank=False)

    manufacturer: "models.ForeignKey[Union[Combinable, Manufacturer], Manufacturer]" = (
        models.ForeignKey(
            Manufacturer, blank=False, null=False, on_delete=models.CASCADE
        )
    )

    is_cartridge: "models.BooleanField[bool, bool]" = models.BooleanField(
        "Cartridge/Blade",
        default=False,
    )

    description: "models.CharField[str, str]" = models.CharField(
        max_length=512,
        blank=True,
    )

    netbox_id: "models.PositiveIntegerField[int, int]" = models.PositiveIntegerField(
        verbose_name="NetBox ID",
        help_text="The ID that NetBox gives to the object.",
        default=0,
    )

    netbox_last_fetch_attempt: "OptionalDateTimeField" = models.DateTimeField(
        "NetBox Last Fetched at",
        null=True,
        blank=True,
    )

    enclosure_set: models.Manager["Enclosure"]
    netboxorthoscomparisionruns: models.Manager["NetboxOrthosComparisionRun"]

    objects = DeviceTypeManager()

    def natural_key(self) -> Tuple[str]:
        return (self.name,)

    natural_key.dependencies = ["data.manufacturer"]  # type: ignore

    def __str__(self) -> str:
        return self.name

    @admin.display(description="Manufacturer")
    def get_manufacturer(self) -> str:
        return self.manufacturer.name

    @admin.display(description="Enclosures")
    def get_enclosure_count(self) -> int:
        return self.enclosure_set.count()

    @classmethod
    def get_device_type_manager(cls) -> DeviceTypeManager:
        """
        Return the enclosure manager.
        """
        return cast(DeviceTypeManager, cls.objects)

    def fetch_netbox_record(self) -> Optional[Dict[str, Any]]:
        """
        Fetch the record of this DeviceType object from NetBox.

        :returns: None in case the record cannot be retrieved. The Dict with the NetBox data otherwhise.
        :raises HTTPError: In case any HTTP code except 200 and 404 is returned.
        """
        netbox_api = Netbox.get_instance()
        try:
            return netbox_api.fetch_device_type(self.netbox_id)
        except HTTPError as e:
            if e.response.status_code == 404:
                logger.info("Fetching DeviceType from NetBox failed with status 404.")
                return None
            raise e

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
            object_type=NetboxOrthosComparisionRun.NetboxOrthosComparisionItemTypes.DEVICE_TYPE,
            object_device_type=self,
        )
        run_obj.save()

        netbox_devicetype = self.fetch_netbox_record()
        if netbox_devicetype is None:
            return

        # Name
        NetboxOrthosComparisionResult(
            run_id=run_obj,
            property_name="name",
            orthos_result=self.name or "<not set>",
            netbox_result=netbox_devicetype.get("model", "<not set>"),
        ).save()
        # Description
        NetboxOrthosComparisionResult(
            run_id=run_obj,
            property_name="description",
            orthos_result=self.description or "<not set>",
            netbox_result=netbox_devicetype.get("description", "<not set>"),
        ).save()

    def fetch_netbox(self) -> None:
        """
        Fetch all information about a device type from NetBox if the NetBox ID is set.
        """
        if self.netbox_id == 0:
            logger.debug("Skipping fetching from NetBox because NetBox ID is 0.")
            return

        self.netbox_last_fetch_attempt = datetime.datetime.now(
            tz=timezone.get_current_timezone()
        )
        self.save()
        netbox_devicetype = self.fetch_netbox_record()
        if netbox_devicetype is None:
            return

        self.name = netbox_devicetype.get("model", self.name)
        self.description = netbox_devicetype.get("description", "")
        self.save()
