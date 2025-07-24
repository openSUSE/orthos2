import datetime
import ipaddress
import logging
import uuid
from typing import TYPE_CHECKING, Optional

from django.db import models
from django.forms import ValidationError

from orthos2.data.models.netboxorthoscomparision import (
    NetboxOrthosComparisionResult,
    NetboxOrthosComparisionRun,
)
from orthos2.data.validators import validate_mac_address
from orthos2.utils.netbox import Netbox

if TYPE_CHECKING:
    from django.db.models.fields.related_descriptors import RelatedManager

    from orthos2.types import (
        MandatoryMachineOneToOneField,
        MandatoryRemotePowerTypeForeignKey,
    )

logger = logging.getLogger("models")


class BMC(models.Model):
    username: "models.CharField[str, str]" = models.CharField(
        max_length=256,
        blank=True,
    )
    password: "models.CharField[str, str]" = models.CharField(
        max_length=256,
        blank=True,
    )
    fqdn: "models.CharField[str, str]" = models.CharField(max_length=256, unique=True)
    mac: "models.CharField[str, str]" = models.CharField(
        max_length=17,
        unique=True,
        validators=[validate_mac_address],
    )

    machine_id: int
    machine: "MandatoryMachineOneToOneField" = models.OneToOneField(
        "data.Machine",
        on_delete=models.CASCADE,
    )

    fence_agent: "MandatoryRemotePowerTypeForeignKey" = models.ForeignKey(
        "data.RemotePowerType",
        on_delete=models.CASCADE,
        verbose_name="Fence agent",
        help_text="Fence agent for remote power control",
        limit_choices_to={"device": "bmc"},
    )

    ip_address_v4: "models.GenericIPAddressField[Optional[str], Optional[str]]" = (
        models.GenericIPAddressField(
            protocol="IPv4",
            blank=True,
            unique=True,
            null=True,
            verbose_name="IPv4 address",
            help_text="IPv4 address",
        )
    )

    ip_address_v6: "models.GenericIPAddressField[Optional[str], Optional[str]]" = (
        models.GenericIPAddressField(
            protocol="IPv6",
            blank=True,
            unique=True,
            null=True,
            verbose_name="IPv6 address",
            help_text="IPv6 address",
        )
    )

    netboxorthoscomparisionruns: "RelatedManager[NetboxOrthosComparisionRun]"

    def natural_key(self) -> str:
        return self.fqdn

    def __str__(self) -> str:
        return self.fqdn

    def compare_netbox(self) -> None:
        """
        Compare the current data in the database of Orthos 2 with the data from NetBox.
        """
        if self.machine.netbox_id == 0:
            logger.debug("Skipping comparision because NetBox ID is 0.")
            return

        run_uuid = uuid.uuid4()
        run_obj = NetboxOrthosComparisionRun(
            run_id=run_uuid,
            compare_timestamp=datetime.datetime.now(),
            object_type=NetboxOrthosComparisionRun.NetboxOrthosComparisionItemTypes.BMC,
            object_bmc=self,
        )
        run_obj.save()
        netbox_api = Netbox.get_instance()
        netbox_interfaces = netbox_api.check_interface_mgmt_by_id(
            self.machine.netbox_id
        )
        for interface in netbox_interfaces:
            if interface.get("primary_mac_address") is None:
                continue
            if interface.get("primary_mac_address", {}).get("display", "") == self.mac:
                # FIXME: A single interface can have any number of IPs (both v4 and v6)
                NetboxOrthosComparisionResult(
                    run_id=run_obj,
                    property_name="mac_address",
                    orthos_result=self.mac,
                    netbox_result=interface.get("primary_mac_address", {}).get(
                        "display", "None"
                    ),
                ).save()
                ips = netbox_api.check_ip_by_interface(interface.get("id"))  # type: ignore
                for ip in ips:
                    ip_obj = ipaddress.ip_network(ip.get("display"))  # type: ignore
                    NetboxOrthosComparisionResult(
                        run_id=run_obj,
                        property_name="fqdn (IPv%s)" % ip_obj.version,
                        orthos_result=self.fqdn,
                        netbox_result=ip.get("dns_name", "None"),
                    ).save()
                    if ip_obj.version == 4:
                        NetboxOrthosComparisionResult(
                            run_id=run_obj,
                            property_name="ip_address_v4",
                            orthos_result=self.ip_address_v4 or "None",
                            netbox_result=str(ip_obj),
                        ).save()
                    if ip_obj.version == 6:
                        NetboxOrthosComparisionResult(
                            run_id=run_obj,
                            property_name="ip_address_v6",
                            orthos_result=self.ip_address_v6 or "None",
                            netbox_result=str(ip_obj),
                        ).save()
        # TODO: Machine
        # TODO: Ethernet Type

    def fetch_netbox(self) -> None:
        """
        Fetch information from Netbox.
        """
        if self.machine.netbox_id == 0:
            logger.debug("Skipping fetching from NetBox because NetBox ID is 0.")
            return
        netbox_api = Netbox.get_instance()
        netbox_interfaces = netbox_api.check_interface_mgmt_by_id(
            self.machine.netbox_id
        )
        # Reset fields
        self.ip_address_v4 = None
        self.ip_address_v6 = None
        # Set fields
        for interface in netbox_interfaces:
            if interface.get("primary_mac_address") is None:
                continue
            if interface.get("primary_mac_address", {}).get("display", "") == self.mac:
                # FIXME: A single interface can have any number of IPs (both v4 and v6)
                ips = netbox_api.check_ip_by_interface(interface.get("id"))  # type: ignore
                for ip in ips:
                    ip_obj = ipaddress.ip_network(ip.get("display"))  # type: ignore
                    if ip_obj.version == 4:
                        self.ip_address_v4 = str(ip_obj)
                    if ip_obj.version == 6:
                        self.ip_address_v6 = str(ip_obj)
                    self.save()

    def clean_fence_agent(self) -> None:
        """
        Validate the fence_agent field to ensure it is of type "hypervisor".
        This method is called automatically by Django's validation system.
        """
        if not self.fence_agent:
            raise ValidationError("Fence name cannot be empty.")
        if self.fence_agent.device != "bmc":  # type: ignore
            raise ValidationError(
                "The fence agent must be of type 'hypervisor'. "
                "Please select a valid fence agent."
            )
