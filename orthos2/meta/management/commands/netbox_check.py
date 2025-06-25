"""
This django admin command will verify that all data that Orthos 2 needs from NetBox is present and can be relied upon.

To do so we will mimic what the NetboxFetchFullMachine Task is doing. For this we assume that all enclosures and
machines have Netbox IDs set.
"""

import logging
from typing import Any, Dict, Optional

from django.core.management import BaseCommand

from orthos2 import settings
from orthos2.data.models import BMC
from orthos2.data.models.networkinterface import NetworkInterface
from orthos2.utils.misc import get_ipv4, get_ipv6
from orthos2.utils.netbox import REST

logger = logging.getLogger("meta")


class NetBoxCheck(REST):
    __object: Optional["NetBoxCheck"] = None

    def __init__(self, host: str, token: str):
        super().__init__(host, token)

    @classmethod
    def get_instance(cls, netbox_url: str, netbox_token: str):
        if cls.__object is None:
            cls.__object = NetBoxCheck(netbox_url, netbox_token)
        return cls.__object

    def fetch_device(self, id: int) -> Dict[str, Any]:
        url = f"{self.base_url}/dcim/devices/{id}/"
        logger.debug("Fetch device data from %s", url)
        data = self.fetcher(url)
        return data

    def fetch_vm(self, id: int) -> Dict[str, Any]:
        url = f"{self.base_url}/virtualization/virtual-machines/{id}/"
        logger.debug(f"Fetch device data from {url}")
        data = self.fetcher(url)
        return data

    def check_mac_address(self, mac: str) -> Dict[str, Any]:
        url = f"{self.base_url}/dcim/interfaces/?mac_address={mac}"
        logger.debug("Checking MAC address from %s", url)
        data = self.fetcher(url)
        return data["results"]

    def check_vm_mac_address(self, mac: str) -> Dict[str, Any]:
        url = f"{self.base_url}/virtualization/interfaces/?mac_address={mac}"
        logger.debug("Checking MAC address from %s", url)
        data = self.fetcher(url)
        return data["results"]

    def check_ip_by_interface(self, id: int) -> Dict[str, Any]:
        url = f"{self.base_url}/ipam/ip-addresses/?interface_id={id}"
        logger.debug("Checking ip address from %s", url)
        data = self.fetcher(url)
        return data["results"]

    def check_ip_by_vm_interface(self, id: int) -> Dict[str, Any]:
        url = f"{self.base_url}/ipam/ip-addresses/?vminterface_id={id}"
        logger.debug("Checking ip address from %s", url)
        data = self.fetcher(url)
        return data["results"]


class Command(BaseCommand):
    help = "Verify that data between NetBox and Orthos2 are in sync"

    def handle(self, *args: Any, **options: Any) -> None:
        """
        Entrypoint for Django to execute the management command.
        """
        netbox_url = settings.NETBOX_URL
        netbox_token = settings.NETBOX_TOKEN
        netbox_api = NetBoxCheck.get_instance(netbox_url, netbox_token)

        # Loop over all Orthos 2 network interfaces and verify their NetBox status
        for intf in NetworkInterface.objects.all():
            orthos_interface_mac: str = intf.mac_address  # type: ignore
            orthos_machine_id: int = intf.machine.id  # type: ignore
            orthos_is_vm: bool = intf.machine.system.virtual  # type: ignore
            orthos_is_diskarray: bool = intf.machine.system.name == "DiskArray"  # type: ignore
            logger.debug(
                "Starting scanning Orthos 2 interface with MAC %s for machine %s",
                orthos_interface_mac,
                intf.machine.fqdn,
            )

            # Case: devlab.pgu1.suse.com must be skipped
            if "devlab.pgu1.suse.com" in intf.machine.fqdn:
                logger.info(
                    "Machine %s Interface %s: Skipping due to being in devlab.pgu1.suse.com",
                    orthos_interface_mac,
                    intf.machine.fqdn,
                )
                continue

            # Case: Filter out vxlan, veth, vlan, rndis_host, cdc_ether, igbvf and iwlwifi interfaces
            if intf.driver_module in (
                "vxlan",
                "veth",
                "vlan",
                "rndis_host",
                "cdc_ether",
                "igbvf",
                "iwlwifi",
            ):
                logger.debug(
                    "Machine %s Interface %s: Skipping due to driver module %s",
                    intf.machine.fqdn,
                    orthos_interface_mac,
                    intf.driver_module,
                )
                continue

            # Case: Skip DiskArrays as we can't display them correctly in Orthos2 atm
            if orthos_is_diskarray:
                logger.info(
                    "Machine %s Interface %s: Skipping due to being a disk array",
                    intf.machine.fqdn,
                    orthos_interface_mac,
                )
                continue

            # Cases:
            # 1. MAC present in NetBox (Interface, VM Interface)
            # 2. Mac not present in NetBox
            netbox_device_interfaces = netbox_api.check_mac_address(
                orthos_interface_mac
            )
            netbox_vm_interfaces = netbox_api.check_vm_mac_address(orthos_interface_mac)

            if len(netbox_device_interfaces) > 0 and len(netbox_vm_interfaces) > 0:
                logger.error(
                    "Machine %s Interface %s: Found ambiguous search results for MAC address",
                    intf.machine.fqdn,
                    orthos_interface_mac,
                )
                continue
            elif len(netbox_device_interfaces) > 0:
                netbox_is_vm = False
            elif len(netbox_vm_interfaces) > 0:
                netbox_is_vm = True
            else:
                logger.error(
                    "Machine %s Interface %s: No MAC addresses found in NetBox",
                    intf.machine.fqdn,
                    orthos_interface_mac,
                )
                continue

            netbox_interfaces = (
                netbox_vm_interfaces if netbox_is_vm else netbox_device_interfaces
            )
            if len(netbox_interfaces) > 1:
                logger.error(
                    "Machine %s Interface %s: Found multiple MAC addresses",
                    intf.machine.fqdn,
                    orthos_interface_mac,
                )
                continue

            netbox_interface = netbox_interfaces[0]

            # Case: Check if NetBox VM is Orthos VM
            if orthos_is_vm != netbox_is_vm:
                logger.warning(
                    "Machine %s Interface %s: Interface is attached to a VM in Orthos but not marked as such in NetBox.",
                    intf.machine.fqdn,
                    orthos_interface_mac,
                )
                continue

            # Cases:
            # 1. MAC address is assigned to an interface on the correct system
            # 2. MAC Address is assigned to an interface on a different system
            if netbox_is_vm:
                netbox_machine = netbox_api.fetch_vm(
                    netbox_interface.get("virtual_machine").get("id")
                )
            else:
                netbox_machine = netbox_api.fetch_device(
                    netbox_interface.get("device").get("id")
                )

            netbox_orthos_id = netbox_machine.get("custom_fields", {}).get("orthos_id")
            if netbox_orthos_id != orthos_machine_id:
                logger.error(
                    "Machine %s Interface %s: Orthos ID and Netbox Orthos ID are not the same (Orthos: '%s'; Netbox: '%s')",
                    intf.machine.fqdn,
                    orthos_interface_mac,
                    orthos_machine_id,
                    netbox_orthos_id,
                )
                continue

            # Cases (only Orthos 2 primary interface):
            # 1. The NetBox interface has the same IPv4 and IPv6 address set as currently Orthos 2 has
            # 2. The NetBox interface has no IPv4/IPv6 set
            # 3. The NetBox interface has a different IPv4/IPv6 set
            # 4. The NetBox interface is missing the IPv4 or IPv6 address
            # 5. The NetBox interface has an incorrect IPv4 or IPv6 address
            if intf.primary:
                orthos_ipv4 = intf.machine.ipv4
                orthos_ipv6 = intf.machine.ipv6

                if netbox_is_vm:
                    netbox_ip_objects = netbox_api.check_ip_by_vm_interface(
                        netbox_interface.get("id")
                    )
                else:
                    netbox_ip_objects = netbox_api.check_ip_by_interface(
                        netbox_interface.get("id")
                    )
                netbox_ips = []
                orthos_ipv4_found = False
                orthos_ipv6_found = False
                for interface in netbox_ip_objects:
                    address = interface.get("address")
                    dns_name = interface.get("dns_name")
                    ip_address = address.split("/")[0]
                    if "/" in address:
                        netbox_ips.append(ip_address)
                    if orthos_ipv4 is not None and ip_address == orthos_ipv4:
                        orthos_ipv4_found = True
                    if orthos_ipv6 is not None and ip_address == orthos_ipv6:
                        orthos_ipv6_found = True
                    # If the primary interface IP (v4/v6) was found and the machine FQDN is not matching
                    if (
                        orthos_ipv4_found or orthos_ipv6_found
                    ) and intf.machine.fqdn != dns_name:
                        logger.error(
                            'Machine %s Interface %s: NetBox and Orthos 2 DNS names are different - %s (Orthos: "%s"; NetBox: "%s")',
                            intf.machine.fqdn,
                            orthos_interface_mac,
                            ip_address,
                            intf.machine.fqdn,
                            dns_name,
                        )
                        continue
                if orthos_ipv4 is not None:
                    if orthos_ipv4 in netbox_ips:
                        netbox_ips.remove(orthos_ipv4)
                    else:
                        logger.error(
                            "Machine %s Interface %s: NetBox interface %s was missing the IPv4 address %s",
                            intf.machine.fqdn,
                            orthos_interface_mac,
                            netbox_interface.get("id"),
                            orthos_ipv4,
                        )
                else:
                    logger.warning(
                        "Machine %s Interface %s: Machine didn't have an IPv4 address in Orthos 2.",
                        intf.machine.fqdn,
                        orthos_interface_mac,
                    )
                if orthos_ipv6 is not None:
                    if orthos_ipv6 in netbox_ips:
                        netbox_ips.remove(orthos_ipv6)
                    else:
                        logger.error(
                            "Machine %s Interface %s: NetBox interface %s was missing the IPv6 address %s",
                            intf.machine.fqdn,
                            orthos_interface_mac,
                            netbox_interface.get("id"),
                            orthos_ipv6,
                        )
                else:
                    logger.warning(
                        "Machine %s Interface %s: Machine didn't have an IPv6 address in Orthos 2.",
                        intf.machine.fqdn,
                        orthos_interface_mac,
                    )
                if len(netbox_ips) > 0:
                    logger.error(
                        "Machine %s Interface %s: NetBox interface %s has leftover IPs: %s",
                        intf.machine.fqdn,
                        orthos_interface_mac,
                        netbox_interface.get("id"),
                        netbox_ips,
                    )

            logger.debug(
                "Ending scanning Orthos 2 interface with MAC %s", orthos_interface_mac
            )

        for bmc in BMC.objects.all():
            orthos_bmc_fqdn: str = bmc.fqdn
            orthos_bmc_mac: str = bmc.mac
            orthos_machine_id: int = bmc.machine.id
            orthos_bmc_ipv4 = get_ipv4(bmc.fqdn)
            orthos_bmc_ipv6 = get_ipv6(bmc.fqdn)

            # Case: devlab.pgu1.suse.com must be skipped
            if "devlab.pgu1.suse.com" in orthos_bmc_fqdn:
                logger.info(
                    "Machine %s BMC Interface %s: Skipping due to being in devlab.pgu1.suse.com",
                    bmc.machine.fqdn,
                    orthos_bmc_mac,
                )
                continue

            # Cases:
            # 1. MAC present in NetBox (Interface, VM Interface)
            # 2. Mac not present in NetBox
            netbox_device_interfaces = netbox_api.check_mac_address(orthos_bmc_mac)
            netbox_vm_interfaces = netbox_api.check_vm_mac_address(orthos_bmc_mac)

            if len(netbox_device_interfaces) > 0 and len(netbox_vm_interfaces) > 0:
                logger.error(
                    "Machine %s BMC Interface %s: Found ambiguous search results for MAC address",
                    bmc.machine.fqdn,
                    orthos_bmc_mac,
                )
                continue
            elif len(netbox_device_interfaces) > 0:
                netbox_is_vm = False
            elif len(netbox_vm_interfaces) > 0:
                netbox_is_vm = True
            else:
                logger.error(
                    "Machine %s BMC Interface %s: No MAC addresses found in NetBox",
                    bmc.machine.fqdn,
                    orthos_bmc_mac,
                )
                continue

            netbox_interfaces = (
                netbox_vm_interfaces if netbox_is_vm else netbox_device_interfaces
            )
            if len(netbox_interfaces) > 1:
                logger.error(
                    "Machine %s BMC Interface %s: Found multiple MAC addresses",
                    bmc.machine.fqdn,
                    orthos_bmc_mac,
                )
                continue

            netbox_interface = netbox_interfaces[0]

            # Cases:
            # 1. MAC address is assigned to an interface on the correct system
            # 2. MAC Address is assigned to an interface on a different system
            if netbox_is_vm:
                netbox_machine = netbox_api.fetch_vm(
                    netbox_interface.get("virtual_machine").get("id")
                )
            else:
                netbox_machine = netbox_api.fetch_device(
                    netbox_interface.get("device").get("id")
                )

            netbox_orthos_id = netbox_machine.get("custom_fields", {}).get("orthos_id")
            if netbox_orthos_id != orthos_machine_id:
                logger.error(
                    "Machine %s BMC Interface %s: Orthos ID and Netbox Orthos ID are not the same (Orthos: '%s'; Netbox: '%s')",
                    bmc.machine.fqdn,
                    orthos_bmc_mac,
                    orthos_machine_id,
                    netbox_orthos_id,
                )
                continue

            # Cases:
            # 1. NetBox Interface is of type "Mgmt only"
            # 2. NetBox Interface is not of type "Mgmt only"
            if not netbox_interface.get("mgmt_only"):
                logger.error(
                    "Machine %s BMC Interface %s: Mgmt Interface in Orthos was not marked as such in NetBox",
                    bmc.machine.fqdn,
                    orthos_bmc_mac,
                )

            # Cases:
            # 1. NetBox Interface has DNS name set
            # 2. NetBox Interface has wrong or no DNS name set

            if netbox_is_vm:
                netbox_ip_objects = netbox_api.check_ip_by_vm_interface(
                    netbox_interface.get("id")
                )
            else:
                netbox_ip_objects = netbox_api.check_ip_by_interface(
                    netbox_interface.get("id")
                )
            netbox_ips = []
            orthos_ipv4_found = False
            orthos_ipv6_found = False
            for interface in netbox_ip_objects:
                address = interface.get("address")
                dns_name = interface.get("dns_name")
                ip_address = address.split("/")[0]
                if "/" in address:
                    netbox_ips.append(ip_address)
                if orthos_bmc_ipv4 is not None and ip_address == orthos_bmc_ipv4:
                    orthos_ipv4_found = True
                if orthos_bmc_ipv6 is not None and ip_address == orthos_bmc_ipv6:
                    orthos_ipv6_found = True
                # If the primary interface IP (v4/v6) was found and the machine FQDN is not matching
                if (orthos_ipv4_found or orthos_ipv6_found) and bmc.fqdn != dns_name:
                    logger.error(
                        'Machine %s BMC Interface %s: NetBox and Orthos 2 DNS names are different - %s (Orthos: "%s"; NetBox: "%s")',
                        bmc.machine.fqdn,
                        orthos_bmc_mac,
                        ip_address,
                        bmc.fqdn,
                        dns_name,
                    )
                    continue
            if orthos_bmc_ipv4 is not None:
                if orthos_bmc_ipv4 in netbox_ips:
                    netbox_ips.remove(orthos_bmc_ipv4)
                else:
                    logger.error(
                        "Machine %s BMC Interface %s: NetBox interface %s was missing the IPv4 address %s",
                        bmc.machine.fqdn,
                        orthos_bmc_mac,
                        netbox_interface.get("id"),
                        orthos_bmc_ipv4,
                    )
            else:
                logger.warning(
                    "Machine %s BMC Interface %s: Machine didn't have an IPv4 address in Orthos 2.",
                    bmc.machine.fqdn,
                    orthos_bmc_mac,
                )
            if orthos_bmc_ipv6 is not None:
                if orthos_bmc_ipv6 in netbox_ips:
                    netbox_ips.remove(orthos_bmc_ipv6)
                else:
                    logger.error(
                        "Machine %s BMC Interface %s: NetBox interface %s was missing the IPv6 address %s",
                        bmc.machine.fqdn,
                        orthos_bmc_mac,
                        netbox_interface.get("id"),
                        orthos_bmc_ipv6,
                    )
            else:
                logger.warning(
                    "Machine %s BMC Interface %s: Machine didn't have an IPv6 address in Orthos 2.",
                    bmc.machine.fqdn,
                    orthos_bmc_mac,
                )
            if len(netbox_ips) > 0:
                logger.error(
                    "Machine %s BMC Interface %s: NetBox interface %s has leftover IPs: %s",
                    bmc.machine.fqdn,
                    orthos_bmc_mac,
                    netbox_interface.get("id"),
                    netbox_ips,
                )
