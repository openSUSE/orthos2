import ipaddress
import logging
from typing import TYPE_CHECKING

from django.db import models

from orthos2.data.validators import validate_mac_address
from orthos2.utils.netbox import Netbox
from orthos2.utils.remotepowertype import get_remote_power_type_choices

if TYPE_CHECKING:
    from orthos2.data.models.machine import Machine

logger = logging.getLogger("models")


class BMC(models.Model):
    username = models.CharField(max_length=256, blank=True)
    password = models.CharField(max_length=256, blank=True)
    fqdn = models.CharField(max_length=256, unique=True)
    mac = models.CharField(
        max_length=17, unique=True, validators=[validate_mac_address]
    )
    machine = models.OneToOneField["Machine"]("data.Machine", on_delete=models.CASCADE)  # type: ignore

    remotepower_type_choices = get_remote_power_type_choices("bmc")
    fence_name = models.CharField(
        choices=remotepower_type_choices, max_length=255, verbose_name="Fence agent"
    )

    ip_address_v4 = models.GenericIPAddressField(
        protocol="IPv4",
        blank=True,
        unique=True,
        null=True,
        verbose_name="IPv4 address",
        help_text="IPv4 address",
    )

    ip_address_v6 = models.GenericIPAddressField(
        protocol="IPv6",
        blank=True,
        unique=True,
        null=True,
        verbose_name="IPv6 address",
        help_text="IPv6 address",
    )

    def natural_key(self) -> str:
        return self.fqdn

    def __str__(self) -> str:
        return self.fqdn

    def fetch_netbox(self):
        """
        TODO
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
                ips = netbox_api.check_ip_by_interface(interface.get("id"))
                self.ip_address_v4 = ""
                self.ip_address_v6 = ""
                for ip in ips:
                    ip_obj = ipaddress.ip_network(ip.get("display"))
                    if ip_obj.version == 4:
                        self.ip_address_v4 = str(ip_obj)
                    if ip_obj.version == 6:
                        self.ip_address_v6 = str(ip_obj)
                    self.save()
