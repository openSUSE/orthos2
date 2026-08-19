import datetime
import logging
import uuid
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple, cast

from django.db import models
from django.utils import timezone
from requests import HTTPError

from orthos2.data.models.netboxorthoscomparision import (
    NetboxOrthosComparisionResult,
    NetboxOrthosComparisionRun,
)
from orthos2.utils.netbox import Netbox

if TYPE_CHECKING:
    from orthos2.data.models.platform import Platform
    from orthos2.types import OptionalDateTimeField

logger = logging.getLogger("models")


class ManufacturerManager(models.Manager["Manufacturer"]):
    def get_by_natural_key(self, name: str) -> "Manufacturer":
        return self.get(name=name)


class Manufacturer(models.Model):
    class Meta:  # type: ignore
        ordering = ["name"]

    name: "models.CharField[str, str]" = models.CharField(
        max_length=100,
        blank=False,
        unique=True,
    )

    description: "models.CharField[str, str]" = models.CharField(
        help_text="Description of the Manufacturer, synchronized from NetBox.",
        max_length=512,
        blank=True,
        editable=False,
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

    platform_set: models.Manager["Platform"]
    netboxorthoscomparisionruns: models.Manager["NetboxOrthosComparisionRun"]

    objects = ManufacturerManager()

    def natural_key(self) -> Tuple[str]:
        return (self.name,)

    def __str__(self) -> str:
        return self.name

    @classmethod
    def get_manufacturer_manager(cls) -> ManufacturerManager:
        """
        Return the manufacturer manager.
        """
        return cast(ManufacturerManager, cls.objects)

    def fetch_netbox_record(self) -> Optional[Dict[str, Any]]:
        """
        Fetch the record of this Manufacturer object from NetBox.

        :returns: None in case the record cannot be retrieved. The Dict with the NetBox data otherwhise.
        :raises HTTPError: In case any HTTP code except 200 and 404 is returned.
        """
        netbox_api = Netbox.get_instance()
        try:
            return netbox_api.fetch_manufacturer(self.netbox_id)
        except HTTPError as e:
            if e.response.status_code == 404:
                logger.info("Fetching Manufacturer from NetBox failed with status 404.")
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
            object_type=NetboxOrthosComparisionRun.NetboxOrthosComparisionItemTypes.MANUFACTURER,
            object_manufacturer=self,
        )
        run_obj.save()

        netbox_manufacturer = self.fetch_netbox_record()
        if netbox_manufacturer is None:
            return

        # Name
        NetboxOrthosComparisionResult(
            run_id=run_obj,
            property_name="name",
            orthos_result=self.name or "<not set>",
            netbox_result=netbox_manufacturer.get("name", "<not set>"),
        ).save()
        # Description
        NetboxOrthosComparisionResult(
            run_id=run_obj,
            property_name="description",
            orthos_result=self.description or "<not set>",
            netbox_result=netbox_manufacturer.get("description", "<not set>"),
        ).save()

    def fetch_netbox(self) -> None:
        """
        Fetch all information about a manufacturer from NetBox if the NetBox ID is set.
        """
        if self.netbox_id == 0:
            logger.debug("Skipping fetching from NetBox because NetBox ID is 0.")
            return

        self.netbox_last_fetch_attempt = datetime.datetime.now(
            tz=timezone.get_current_timezone()
        )
        self.save()
        netbox_manufacturer = self.fetch_netbox_record()
        if netbox_manufacturer is None:
            return

        self.name = netbox_manufacturer.get("name", self.name)
        self.description = netbox_manufacturer.get("description", "")
        self.save()
