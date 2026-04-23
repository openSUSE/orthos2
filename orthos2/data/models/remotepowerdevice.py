import datetime
import ipaddress
import logging
import uuid
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple, cast

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.forms import ValidationError
from django.utils import timezone
from requests import HTTPError

from orthos2.data.models import Architecture, Domain
from orthos2.data.models.netboxorthoscomparision import (
    NetboxOrthosComparisionResult,
    NetboxOrthosComparisionRun,
)
from orthos2.data.models.serverconfig import ServerConfig
from orthos2.data.validators import validate_mac_address
from orthos2.utils.netbox import Netbox

if TYPE_CHECKING:
    from orthos2.types import (
        MandatoryArchitectureForeignKey,
        MandatoryDomainForeignKey,
        MandatoryRemotePowerTypeForeignKey,
        OptionalDateTimeField,
    )

logger = logging.getLogger("models")


class RemotePowerDeviceManager(models.Manager["RemotePowerDevice"]):
    """
    Custom manager for RemotePowerDevice to provide additional methods if needed.
    """

    def get_by_natural_key(self, fqdn: str) -> "RemotePowerDevice":
        """
        Get a RemotePowerDevice instance by its natural key (fqdn).
        """
        return self.get(fqdn=fqdn)


class RemotePowerDevice(models.Model):
    # Annotate to allow type checking of autofield
    id: int

    username: "models.CharField[Optional[str], Optional[str]]" = models.CharField(
        max_length=256,
        blank=False,
        null=True,
    )
    password: "models.CharField[Optional[str], Optional[str]]" = models.CharField(
        max_length=256,
        blank=False,
        null=True,
    )
    fqdn: "models.CharField[str, str]" = models.CharField(max_length=256, unique=True)
    mac: "models.CharField[str, str]" = models.CharField(
        max_length=17,
        unique=True,
        validators=[validate_mac_address],
    )
    url: "models.URLField[str, str]" = models.URLField(
        blank=True,
        help_text="URL of the Webinterface to configure this Power Device.<br>"
        " Power devices should be in a separate management network only reachable via the cobbler server.<br>"
        " In this case the Webinterface might be port forwarded, also check Documentation<br>",
    )

    fence_agent: "MandatoryRemotePowerTypeForeignKey" = models.ForeignKey(
        "data.RemotePowerType",
        on_delete=models.CASCADE,
        verbose_name="Fence agent",
        limit_choices_to={"device": "rpowerdevice"},
    )

    architecture: "MandatoryArchitectureForeignKey" = models.ForeignKey(
        Architecture,
        on_delete=models.CASCADE,
    )

    ip_address_v4: "models.GenericIPAddressField[Optional[str], Optional[str]]" = (
        models.GenericIPAddressField(
            protocol="IPv4",
            unique=True,
            null=True,
            blank=True,
            verbose_name="IPv4 address",
            help_text="IPv4 address",
        )
    )

    ip_address_v6: "models.GenericIPAddressField[Optional[str], Optional[str]]" = (
        models.GenericIPAddressField(
            protocol="IPv6",
            unique=True,
            null=True,
            blank=True,
            verbose_name="IPv6 address",
            help_text="IPv6 address",
        )
    )

    domain: "MandatoryDomainForeignKey" = models.ForeignKey(
        Domain,
        on_delete=models.CASCADE,
        help_text="The domain name of the primary NIC",
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

    objects = RemotePowerDeviceManager()

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        documentation_url: str = ServerConfig.get_server_config_manager().by_key(  # type: ignore
            "orthos.documentation.url",
            "http://localhost",
        )
        power_doc = documentation_url + "/" + "powerswitches.html"
        self._meta.get_field("url").help_text += (  # type: ignore
            '<a href="' + power_doc + '" target="_blank"></a><br>'
        )
        super().__init__(*args, **kwargs)

    @staticmethod
    def get_by_str(fqdn_dev: str) -> Optional["RemotePowerDevice"]:
        if not fqdn_dev:
            return None
        fqdn = fqdn_dev.split("[")[0]
        try:
            return RemotePowerDevice.objects.get(fqdn=fqdn)  # type: ignore
        except ObjectDoesNotExist:
            return None

    def natural_key(self) -> Tuple[str]:
        return (self.fqdn,)

    def __str__(self) -> str:
        return self.fqdn + "[" + self.fence_agent.name + "]"

    @classmethod
    def get_remotepowerdevice_manager(cls) -> RemotePowerDeviceManager:
        """
        Return the RemotePowerDeviceManager instance.
        """
        return cast(RemotePowerDeviceManager, cls.objects)

    def clean_fence_agent(self) -> None:
        """
        Validate the fence_agent field to ensure it is of type "hypervisor".
        This method is called automatically by Django's validation system.
        """
        if not self.fence_agent:
            raise ValidationError("Fence name cannot be empty.")
        if self.fence_agent.device != "rpower_device":  # type: ignore
            raise ValidationError(
                "The fence agent must be of type 'hypervisor'. "
                "Please select a valid fence agent."
            )

    def fetch_netbox_record(self) -> Optional[Dict[str, Any]]:
        """
        Fetch the record of this RemotePowerDevice object.
        """
        netbox_api = Netbox.get_instance()
        try:
            netbox_device = netbox_api.fetch_device(self.netbox_id)
        except HTTPError as e:
            if e.response.status_code == 404:
                logger.info("Fetching Device from NetBox failed with status 404.")
                return None
            raise e
        return netbox_device

    def fetch_netbox(self) -> None:
        """
        Fetch information from Netbox.
        """
        if self.netbox_id == 0:
            logger.debug("Skipping fetching from NetBox because NetBox ID is 0.")
            return

        self.netbox_last_fetch_attempt = datetime.datetime.now(
            tz=timezone.get_current_timezone()
        )
        self.save()
        netbox_device = self.fetch_netbox_record()
        if netbox_device is None:
            return

        netbox_api = Netbox.get_instance()
        mgmt_interfaces = netbox_api.check_interface_mgmt_by_id(self.netbox_id)
        if not mgmt_interfaces:
            mgmt_interfaces = netbox_api.check_interface_no_mgmt_by_id(self.netbox_id)

        for interface in mgmt_interfaces:
            primary_mac = interface.get("primary_mac_address")
            if primary_mac is None:
                continue
            ipv4_addresses = netbox_api.check_ip_by_interface_family(interface.get("id"), 4)  # type: ignore
            ipv6_addresses = netbox_api.check_ip_by_interface_family(interface.get("id"), 6)  # type: ignore

            self.mac = primary_mac.get("mac_address")
            if len(ipv4_addresses) > 0:
                self.ip_address_v4 = str(
                    ipaddress.ip_network(ipv4_addresses[0].get("address")).network_address  # type: ignore
                )
            if len(ipv6_addresses) > 0:
                self.ip_address_v6 = str(
                    ipaddress.ip_network(ipv6_addresses[0].get("address")).network_address  # type: ignore
                )
            break

        self.save()

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
            object_type=NetboxOrthosComparisionRun.NetboxOrthosComparisionItemTypes.REMOTE_POWER_DEVICE,
            object_remote_power_device=self,
        )
        run_obj.save()

        netbox_device = self.fetch_netbox_record()
        if netbox_device is None:
            return

        netbox_api = Netbox.get_instance()
        mgmt_interfaces = netbox_api.check_interface_mgmt_by_id(self.netbox_id)
        if not mgmt_interfaces:
            mgmt_interfaces = netbox_api.check_interface_no_mgmt_by_id(self.netbox_id)

        if mgmt_interfaces:
            interface = mgmt_interfaces[0]
            primary_mac = interface.get("primary_mac_address")
            if primary_mac:
                NetboxOrthosComparisionResult(
                    run_id=run_obj,
                    property_name="mac",
                    orthos_result=self.mac,
                    netbox_result=primary_mac.get("mac_address", "<not set>"),
                ).save()

            ipv4_addresses = netbox_api.check_ip_by_interface_family(interface.get("id"), 4)  # type: ignore
            if ipv4_addresses:
                NetboxOrthosComparisionResult(
                    run_id=run_obj,
                    property_name="ip_address_v4",
                    orthos_result=self.ip_address_v4 or "<not set>",
                    netbox_result=str(
                        ipaddress.ip_network(ipv4_addresses[0].get("address")).network_address  # type: ignore
                    ),
                ).save()

            ipv6_addresses = netbox_api.check_ip_by_interface_family(interface.get("id"), 6)  # type: ignore
            if ipv6_addresses:
                NetboxOrthosComparisionResult(
                    run_id=run_obj,
                    property_name="ip_address_v6",
                    orthos_result=self.ip_address_v6 or "<not set>",
                    netbox_result=str(
                        ipaddress.ip_network(ipv6_addresses[0].get("address")).network_address  # type: ignore
                    ),
                ).save()
