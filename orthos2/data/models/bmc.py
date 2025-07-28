import datetime
import ipaddress
import logging
import uuid
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from django.db import models
from django.forms import ValidationError
from django.utils import timezone

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

    def fetch_netbox_record(self) -> Dict[str, Any]:
        """
        Fetch the NetBox record of this NetworkInterface objects. This will attempt to search either the Virtual Machine
        or DCIM endpoint, depending on the System type of the machine.

        :returns: An empty dict in case no network interface could be found in NetBox that matches the MAC of this
                  interface.
        """
        netbox_api = Netbox.get_instance()
        if self.machine.system.virtual:
            netbox_interfaces = netbox_api.check_vm_interface_by_id(
                self.machine.netbox_id
            )
        else:
            netbox_interfaces = netbox_api.check_interface_no_mgmt_by_id(
                self.machine.netbox_id
            )
        netbox_interface = {}
        for interface in netbox_interfaces:
            if interface.get("primary_mac_address") is None:
                continue
            if interface.get("primary_mac_address", {}).get("display", "") == self.mac:
                netbox_interface = interface
                break
        return netbox_interface

    def fetch_netbox_ips(self, interface_id: int) -> List[Dict[str, Any]]:
        """
        Fetch the IPs that are assigned to a given network interface in NetBox.
        """
        netbox_api = Netbox.get_instance()
        if self.machine.system.virtual:
            return netbox_api.check_ip_by_vm_interface(interface_id)
        else:
            return netbox_api.check_ip_by_interface(interface_id)

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
            compare_timestamp=datetime.datetime.now(tz=timezone.get_current_timezone()),
            object_type=NetboxOrthosComparisionRun.NetboxOrthosComparisionItemTypes.BMC,
            object_bmc=self,
        )
        run_obj.save()

        netbox_machine = self.machine.fetch_netbox_record()
        if netbox_machine is None:
            return
        netbox_interface = self.fetch_netbox_record()
        if len(netbox_interface.keys()) == 0:
            logger.warning(
                "Interface with MAC %s could not be found in NetBox.", self.mac
            )
            return

        # FIXME: A single interface can have any number of IPs (both v4 and v6)
        NetboxOrthosComparisionResult(
            run_id=run_obj,
            property_name="mac_address",
            orthos_result=self.mac,
            netbox_result=netbox_interface.get("primary_mac_address", {}).get(
                "display", "None"
            ),
        ).save()
        ips = self.fetch_netbox_ips(netbox_interface.get("id"))  # type: ignore
        if len(ips) == 0:
            logger.debug("No IPs assigned to this interface in NetBox.")
            return
        if len(ips) > 2:
            logger.warning("Too many IPs assigned to this interface in NetBox.")
            return

        # OOB IP
        machine_primary_oob = netbox_machine.get("oob_ip", "<not set>")
        # Virtual machines don't have out-of-band IPs
        if not self.machine.system.virtual:
            NetboxOrthosComparisionResult(
                run_id=run_obj,
                property_name="NetBox Out-Of-Band IP set?",
                orthos_result="",
                netbox_result=str((machine_primary_oob != "")),
            ).save()
        # IPs
        for ip in ips:
            ip_obj = ipaddress.ip_network(ip.get("display"))  # type: ignore
            NetboxOrthosComparisionResult(
                run_id=run_obj,
                property_name="fqdn (IPv%s)" % ip_obj.version,
                orthos_result=self.fqdn,
                netbox_result=ip.get("dns_name", "<not set>"),
            ).save()
            if ip_obj.version == 4:
                NetboxOrthosComparisionResult(
                    run_id=run_obj,
                    property_name="ip_address_v4",
                    orthos_result=self.ip_address_v4 or "<not set>",
                    netbox_result=str(ip_obj),
                ).save()
            if ip_obj.version == 6:
                NetboxOrthosComparisionResult(
                    run_id=run_obj,
                    property_name="ip_address_v6",
                    orthos_result=self.ip_address_v6 or "<not set>",
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

        netbox_interface = self.fetch_netbox_record()
        if len(netbox_interface.keys()) == 0:
            logger.warning(
                "Interface with MAC %s could not be found in NetBox.", self.mac
            )
            return
        ips = self.fetch_netbox_ips(netbox_interface.get("id"))  # type: ignore
        if len(ips) == 0:
            logger.debug("No IPs assigned to this interface in NetBox.")
            return
        if len(ips) > 2:
            logger.warning("Too many IPs assigned to this interface in NetBox.")
            return

        # Reset fields
        self.ip_address_v4 = None
        self.ip_address_v6 = None
        # Set fields
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
        if self.fence_agent.device != "bmc":
            raise ValidationError(
                "The fence agent must be of type 'bmc'. "
                "Please select a valid fence agent."
            )
