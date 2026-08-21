import datetime
import ipaddress
import logging
import uuid
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from django.core.exceptions import ValidationError
from django.db import models
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
        OptionalDateTimeField,
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

    netbox_last_fetch_attempt: "OptionalDateTimeField" = models.DateTimeField(
        "NetBox Last Fetched at",
        null=True,
        blank=True,
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
            netbox_interfaces = netbox_api.check_interface_mgmt_by_id(
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
                orthos_result="True",
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
                    netbox_result=str(ip_obj).split("/", 1)[0],
                ).save()
            if ip_obj.version == 6:
                NetboxOrthosComparisionResult(
                    run_id=run_obj,
                    property_name="ip_address_v6",
                    orthos_result=self.ip_address_v6 or "<not set>",
                    netbox_result=str(ip_obj).split("/", 1)[0],
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

        self.netbox_last_fetch_attempt = datetime.datetime.now(
            tz=timezone.get_current_timezone()
        )
        self.save()
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

    def clean(self) -> None:
        """Validate credentials, network membership and cross-model uniqueness."""
        if self.username and not self.password:
            raise ValidationError("Username also needs a password!")
        if self.password and not self.username:
            raise ValidationError("Password also needs a username!")

        from orthos2.data.models.networkinterface import NetworkInterface

        if NetworkInterface.objects.filter(mac_address=self.mac).exists():
            raise ValidationError(
                "MAC address '{}' is already in use by a network interface!".format(
                    self.mac
                )
            )
        if (
            self.ip_address_v4
            and NetworkInterface.objects.filter(
                ip_address_v4=self.ip_address_v4
            ).exists()
        ):
            raise ValidationError(
                "IPv4 address '{}' is already in use by a network interface!".format(
                    self.ip_address_v4
                )
            )
        if (
            self.ip_address_v6
            and NetworkInterface.objects.filter(
                ip_address_v6=self.ip_address_v6
            ).exists()
        ):
            raise ValidationError(
                "IPv6 address '{}' is already in use by a network interface!".format(
                    self.ip_address_v6
                )
            )

        if (
            (self.ip_address_v4 or self.ip_address_v6)
            and self.machine_id is not None
            and not self.machine.administrative
        ):
            from orthos2.data.models.domain import Domain
            from orthos2.utils.misc import get_domain

            try:
                bmc_domain = Domain.objects.get(name=get_domain(self.fqdn))
            except Domain.DoesNotExist:
                return

            bmc_network_v4 = ipaddress.ip_network(
                f"{bmc_domain.ip_v4}/{bmc_domain.subnet_mask_v4}", strict=False
            )
            bmc_network_v6 = ipaddress.ip_network(
                f"{bmc_domain.ip_v6}/{bmc_domain.subnet_mask_v6}", strict=False
            )
            if (
                self.ip_address_v4
                and ipaddress.ip_address(self.ip_address_v4) not in bmc_network_v4
            ):
                raise ValidationError("IPv4 address is not in the chosen network!")
            if (
                self.ip_address_v6
                and ipaddress.ip_address(self.ip_address_v6) not in bmc_network_v6
            ):
                raise ValidationError("IPv6 address is not in the chosen network!")

    def save(self, *args: Any, **kwargs: Any) -> None:
        super().save(*args, **kwargs)
        if self.machine.bmc_allowed() and not self.machine.has_remotepower():
            from orthos2.data.models.remotepower import RemotePower

            RemotePower(machine=self.machine).save()
