# pyright: reportUnusedVariable=false
from typing import Any, Dict

import requests

from orthos2.utils.netbox import Netbox


class NetboxSetup(Netbox):
    def post_custom_field_choice_sets(self, data: Dict[str, Any]):
        url = f"{self.base_url}/extras/custom-field-choice-sets/"
        return self.uploader(data, url)

    def post_custom_fields(self, data: Dict[str, Any]):
        url = f"{self.base_url}/extras/custom-fields/"
        return self.uploader(data, url)

    def post_site_group(self, data: Dict[str, Any]):
        url = f"{self.base_url}/dcim/site-groups/"
        return self.uploader(data, url)

    def post_site(self, data: Dict[str, Any]):
        url = f"{self.base_url}/dcim/sites/"
        return self.uploader(data, url)

    def post_region(self, data: Dict[str, Any]):
        url = f"{self.base_url}/dcim/regions/"
        return self.uploader(data, url)

    def post_location(self, data: Dict[str, Any]):
        url = f"{self.base_url}/dcim/locations/"
        return self.uploader(data, url)

    def post_rack(self, data: Dict[str, Any]):
        url = f"{self.base_url}/dcim/racks/"
        return self.uploader(data, url)

    def post_device_role(self, data: Dict[str, Any]):
        url = f"{self.base_url}/dcim/device-roles/"
        return self.uploader(data, url)

    def post_platform(self, data: Dict[str, Any]):
        url = f"{self.base_url}/dcim/platforms/"
        return self.uploader(data, url)

    def post_manufacturer(self, data: Dict[str, Any]):
        url = f"{self.base_url}/dcim/manufacturers/"
        return self.uploader(data, url)

    def post_device_type(self, data: Dict[str, Any]):
        url = f"{self.base_url}/dcim/device-types/"
        return self.uploader(data, url)

    def post_mac(self, data: Dict[str, Any]):
        url = f"{self.base_url}/dcim/mac-addresses/"
        return self.uploader(data, url)

    def patch_mac(self, id: int, data: Dict[str, Any]):
        url = f"{self.base_url}/dcim/mac-addresses/{id}/"
        return self.patcher(data, url)

    def patch_device(self, id: int, data: Dict[str, Any]):
        url = f"{self.base_url}/dcim/devices/{id}/"
        print(f"Patching device data from {url} with {data}")
        return self.patcher(data, url)

    def patch_vm(self, id: int, data: Dict[str, Any]):
        url = f"{self.base_url}/virtualization/virtual-machines/{id}/"
        print("Patching device data from {}".format(url))
        return self.patcher(data, url)

    def patch_vmcluster(self, id: int, data: Dict[str, Any]):
        url = f"{self.base_url}/virtualization/clusters/{id}/"
        print("Patching device data from {}".format(url))
        return self.patcher(data, url)

    def patch_interface(self, id: int, data: Dict[str, Any]):
        url = f"{self.base_url}/dcim/interfaces/{id}/"
        print(f"Patching interface from {url} with {data}")
        return self.patcher(data, url)

    def patch_vm_interface(self, id: int, data: Dict[str, Any]):
        url = f"{self.base_url}/virtualization/interfaces/{id}/"
        print(f"Patching interface from {url} with {data}")
        return self.patcher(data, url)

    def patch_console_port(self, id: int, data: Dict[str, Any]):
        url = f"{self.base_url}/dcim/console-ports/{id}/"
        print(f"Patching console port data from {url} with {data}")
        return self.patcher(data, url)

    def patch_console_server_port(self, id: int, data: Dict[str, Any]):
        url = f"{self.base_url}/dcim/console-server-ports/{id}/"
        print(f"Patching console server port data from {url} with {data}")
        return self.patcher(data, url)

    def patch_power_port(self, id: int, data: Dict[str, Any]):
        url = f"{self.base_url}/dcim/power-ports/{id}/"
        print(f"Patching power port data from {url} with {data}")
        return self.patcher(data, url)

    def patch_power_outlet(self, id: int, data: Dict[str, Any]):
        url = f"{self.base_url}/dcim/power-outlets/{id}/"
        print(f"Patching power outlet data from {url} with {data}")
        return self.patcher(data, url)

    def patch_ip(self, id: int, data: Dict[str, Any]):
        url = f"{self.base_url}/ipam/ip-addresses/{id}/"
        print(f"Patching ip address from {url}")
        return self.patcher(data, url)

    def delete_device(self, dev: int):
        url = f"{self.base_url}/dcim/devices/{dev}/"
        print(f"Deleting device from {url}")
        self.deleter(url)

    def delete_contact_assignments(self, id: int):
        url = f"{self.base_url}/tenancy/contact-assignments/{id}/"
        print(f"Deleting contact assignment from {url}")
        self.deleter(url)

    def delete_cable(self, id: int):
        url = f"{self.base_url}/dcim/cables/{id}/"
        print(f"Deleting cable from {url}")
        self.deleter(url)

    def post_contact_assignments(self, data: Dict[str, Any]):
        url = f"{self.base_url}/tenancy/contact-assignments/"
        print("Uploading tenancy assignments data to {}".format(url))
        self.uploader(data, url)

    def post_interface(self, data: Dict[str, Any]):
        url = f"{self.base_url}/dcim/interfaces/"
        print("Posting Interface data to {}".format(url))
        return self.uploader(data, url)

    def post_vm_interface(self, data: Dict[str, Any]):
        url = f"{self.base_url}/virtualization/interfaces/"
        print("Posting Interface data to {}".format(url))
        return self.uploader(data, url)

    def post_module_interface(self, data: Dict[str, Any]):
        url = f"{self.base_url}/dcim/modules/"
        print("Posting Interface data to {}".format(url))
        return self.uploader(data, url)

    def post_power_port(self, data: Dict[str, Any]):
        url = f"{self.base_url}/dcim/power-ports/"
        print("Posting power port data to {}".format(url))
        return self.uploader(data, url)

    def post_power_outlet(self, data: Dict[str, Any]):
        url = f"{self.base_url}/dcim/power-outlets/"
        print("Posting power outlet data to {}".format(url))
        return self.uploader(data, url)

    def post_console_port(self, data: Dict[str, Any]):
        url = f"{self.base_url}/dcim/console-ports/"
        print("Posting console port data to {}".format(url))
        return self.uploader(data, url)

    def post_console_server_port(self, data: Dict[str, Any]):
        url = f"{self.base_url}/dcim/console-server-ports/"
        print("Posting console server port data to {}".format(url))
        return self.uploader(data, url)

    def post_ip(self, data: Dict[str, Any]):
        url = f"{self.base_url}/ipam/ip-addresses/"
        print(f"Posting IP data to {url}")
        return self.uploader(data, url)

    def post_prefix(self, data: Dict[str, Any]):
        url = f"{self.base_url}/ipam/prefixes/"
        print(f"Posting prefix data to {url}")
        return self.uploader(data, url)

    def post_device(self, data: Dict[str, Any]):
        url = f"{self.base_url}/dcim/devices/"
        print(f"Posting device data to {url}")
        return self.uploader(data, url)

    def post_vm(self, data: Dict[str, Any]):
        url = f"{self.base_url}/virtualization/virtual-machines/"
        print(f"Posting VM data to {url}")
        return self.uploader(data, url)

    def post_cluster_type(self, data: Dict[str, Any]):
        url = f"{self.base_url}/virtualization/cluster-types/"
        print(f"Posting cluster type {data} to {url}")
        return self.uploader(data, url)

    def post_cluster(self, data: Dict[str, Any]):
        url = f"{self.base_url}/virtualization/clusters/"
        print(f"Posting cluster data {data} to {url}")
        return self.uploader(data, url)

    def post_virtual_machine(self, data: Dict[str, Any]):
        url = f"{self.base_url}/virtualization/virtual-machines/"
        print(f"Posting virtual machine data {data} to {url}")
        return self.uploader(data, url)


def assign_mac_address_to_interface(
    netbox: NetboxSetup, mac_address: Dict[str, Any], network_interface: Dict[str, Any]
) -> None:
    try:
        netbox.patch_mac(
            int(mac_address.get("id", -1)),
            {
                "assigned_object_id": network_interface.get("id"),
                "assigned_object_type": "dcim.interface",
            },
        )
    except requests.exceptions.RequestException:
        pass
    try:
        netbox.patch_interface(
            int(network_interface.get("id", -1)),
            {"primary_mac_address": mac_address.get("id")},
        )
    except requests.exceptions.RequestException:
        pass


def assign_ip_address_to_interface(
    netbox: NetboxSetup, ip_address: Dict[str, Any], interface: Dict[str, Any]
) -> None:
    netbox.patch_ip(
        int(ip_address.get("id", -1)),
        {
            "assigned_object_type": "dcim.interface",
            "assigned_object_id": interface.get("id"),
        },
    )


def create_device_type(
    netbox: NetboxSetup,
    model: str,
    slug: str,
    height: float,
    manufacturer: Dict[str, Any],
) -> Dict[str, Any]:
    result_device_type: Dict[str, Any] = {}
    try:
        result_device_type = netbox.post_device_type(
            {
                "model": model,
                "slug": slug,
                "u_height": height,
                "manufacturer": {
                    "name": manufacturer.get("name"),
                    "slug": manufacturer.get("slug"),
                },
            }
        )
    except requests.exceptions.RequestException:
        pass
    return result_device_type


def create_interface(
    netbox: NetboxSetup, device_name: str, interface_name: str, mgmt_only: bool = False
) -> Dict[str, Any]:
    interface: Dict[str, Any] = {}
    try:
        interface = netbox.post_interface(
            {
                "device": {"name": device_name},
                "name": interface_name,
                "type": "1000base-t",
                "mgmt_only": mgmt_only,
            }
        )
    except requests.exceptions.RequestException:
        pass
    return interface


def create_manufacturer(netbox: NetboxSetup, name: str, slug: str) -> Dict[str, Any]:
    result_manufacturer: Dict[str, Any] = {}
    try:
        result_manufacturer = netbox.post_manufacturer({"name": name, "slug": slug})
    except requests.exceptions.RequestException:
        pass
    return result_manufacturer


def create_mac_address(netbox: NetboxSetup, mac_address: str) -> Dict[str, Any]:
    result_mac_address: Dict[str, Any] = {}
    try:
        result_mac_address = netbox.post_mac({"mac_address": mac_address})
    except requests.exceptions.RequestException:
        pass
    return result_mac_address


def create_prefix(netbox: NetboxSetup, prefix: str) -> Dict[str, Any]:
    result_prefix: Dict[str, Any] = {}
    try:
        result_prefix = netbox.post_prefix({"prefix": prefix})
    except requests.exceptions.RequestException:
        pass
    return result_prefix


def create_ip_address(
    netbox: NetboxSetup, ip_address: str, dns_name: str
) -> Dict[str, Any]:
    result_ip_address: Dict[str, Any] = {}
    try:
        result_ip_address = netbox.post_ip(
            {"address": ip_address, "dns_name": dns_name}
        )
    except requests.exceptions.RequestException:
        pass
    return result_ip_address


def create_device(
    netbox: NetboxSetup,
    name: str,
    manufacturer: Dict[str, Any],
    device_type: Dict[str, Any],
    device_role: Dict[str, Any],
    site: Dict[str, Any],
) -> Dict[str, Any]:
    result_device: Dict[str, Any] = {}
    try:
        result_device = netbox.post_device(
            {
                "name": name,
                "device_type": {
                    "manufacturer": {
                        "name": manufacturer.get("name"),
                        "slug": manufacturer.get("slug"),
                    },
                    "model": device_type.get("model"),
                    "slug": device_type.get("slug"),
                },
                "role": {
                    "name": device_role.get("name"),
                    "slug": device_role.get("slug"),
                },
                "site": {"name": site.get("name"), "slug": site.get("slug")},
            }
        )
    except requests.exceptions.RequestException:
        pass
    return result_device


def main():
    # Disable this to allow for easier script development
    # pylint: disable=locally-disabled
    # pylint: disable=unused-variable
    netbox = NetboxSetup(
        host="http://netbox.orthos2.test:8080",
        token="efa8c297936bd152cde34326e26d6b866de03fad",
    )

    # Create Custom Field Choice Set
    try:
        netbox.post_custom_field_choice_sets(
            {
                "name": "arch choices",
                "extra_choices": [
                    ["aarch64", "aarch64"],
                    ["i386", "i386"],
                    ["ia64", "ia64"],
                    ["ppc64", "ppc64"],
                    ["ppc64le", "ppc64le"],
                    ["riscv64", "riscv64"],
                    ["s390x", "s390x"],
                    ["x86_64", "x86_64"],
                ],
                "order_alphabetically": True,
            }
        )
    except requests.exceptions.RequestException:
        pass
    # Create Custom Field Choice Set
    try:
        netbox.post_custom_field_choice_sets(
            {
                "name": "fence agent choices",
                "extra_choices": [
                    ["redfish", "redfish"],
                    ["ipmilanplus", "ipmilanplus"],
                ],
                "order_alphabetically": True,
            }
        )
    except requests.exceptions.RequestException:
        pass
    # Create Custom Field "arch"
    try:
        netbox.post_custom_fields(
            {
                "name": "arch",
                "label": "CPU Architecture",
                "object_types": ["dcim.device", "virtualization.virtualmachine"],
                "type": "select",
                "choice_set": {"name": "arch choices"},
            }
        )
    except requests.exceptions.RequestException:
        pass
    # Create Custom Field "product_code"
    try:
        netbox.post_custom_fields(
            {
                "name": "product_code",
                "label": "Product Code",
                "object_types": ["dcim.device"],
                "type": "text",
            }
        )
    except requests.exceptions.RequestException:
        pass
    # Create Custom Field "fence agent"
    try:
        netbox.post_custom_fields(
            {
                "name": "fence_agent",
                "label": "Fence Agent",
                "object_types": ["dcim.interface"],
                "type": "select",
                "choice_set": {"name": "fence agent choices"},
            }
        )
    except requests.exceptions.RequestException:
        pass
    # Create Site Group
    try:
        netbox.post_site_group(
            {"name": "orthos2-site-group", "slug": "orthos2-site-group"}
        )
    except requests.exceptions.RequestException:
        pass
    # Create Site
    try:
        site_orthos2 = netbox.post_site(
            {"name": "orthos2-site", "slug": "orthos2-site"}
        )
    except requests.exceptions.RequestException as exec:
        raise RuntimeError(
            "Creating a site must be succesful in order for the setup script to work!"
        ) from exec
    # Create Region
    try:
        netbox.post_region({"name": "orthos2-region", "slug": "orthos2-region"})
    except requests.exceptions.RequestException:
        pass
    # Create Location
    try:
        netbox.post_location(
            {
                "name": "orthos2-location",
                "slug": "orthos2-location",
                "site": {"name": "orthos2-site", "slug": "orthos2-site"},
            }
        )
    except requests.exceptions.RequestException:
        pass
    # Create Rack
    try:
        netbox.post_rack(
            {
                "name": "orthos2-rack",
                "site": {"name": "orthos2-site", "slug": "orthos2-site"},
            }
        )
    except requests.exceptions.RequestException:
        pass
    # Create Role
    try:
        device_role_server = netbox.post_device_role(
            {
                "display": "Server",
                "name": "Server",
                "slug": "server",
                "color": "9e9e9e",
                "vm_role": True,
                "description": "",
            }
        )
    except requests.exceptions.RequestException as exec:
        raise RuntimeError(
            "Creating a device role must be successful in order for the setup script to work!"
        ) from exec
    # Create Platform
    try:
        netbox.post_platform(
            {"name": "SUSE Linux (Unknown Release)", "slug": "suse-unknown"}
        )
    except requests.exceptions.RequestException:
        pass
    # Create Prefix
    prefix_ipv4 = create_prefix(netbox, "192.0.2.0/24")
    prefix_ipv6 = create_prefix(netbox, "2001:db8::/32")
    # Create IP Address - With DNS Name
    ip_address_v4_primary = create_ip_address(
        netbox, "192.0.2.2/32", "example.orthos2.test"
    )
    ip_address_v6_primary = create_ip_address(
        netbox, "2001:db8::2/128", "example.orthos2.test"
    )
    ip_address_v4_oob = create_ip_address(
        netbox, "192.0.2.3/32", "example-sp.orthos2.test"
    )
    ip_address_v6_oob = create_ip_address(
        netbox, "2001:db8::3/128", "example-sp.orthos2.test"
    )
    # Create Manufacturer
    manufacturer_ibmz = create_manufacturer(netbox, "IBM zSeries", "ibm-zseries")
    manufacturer_ibmpower = create_manufacturer(
        netbox, "IBM Power System", "ibm-power-system"
    )
    manufacturer_ampere = create_manufacturer(netbox, "Ampere", "ampere")
    manufacturer_amd = create_manufacturer(netbox, "AMD", "amd")
    # Create Device Types (normal Server, PPC, S390X, aarch64)
    device_type_ibm_z13 = create_device_type(
        netbox, "z13", "z13", 42.0, manufacturer_ibmz
    )
    device_type_ibm_z13_lpar = create_device_type(
        netbox,
        "z13 LPAR",
        "z13-lpar",
        0.0,
        manufacturer_ibmz,
    )
    device_type_ibm_power_10_chassis = create_device_type(
        netbox,
        "Power10 S1022 (9105-22A) Chassis",
        "power10-s1022-9105-22a-chassis",
        2.0,
        manufacturer_ibmpower,
    )
    device_type_ibm_power_10_lpar = create_device_type(
        netbox,
        "Power10 S1022 (9105-22A)",
        "power10-s1022-9105-22a",
        0.0,
        manufacturer_ibmpower,
    )
    device_type_ampere_mt_jade = create_device_type(
        netbox, "Mt. Jade", "ampere-mt-jade", 1.0, manufacturer_ampere
    )
    device_type_amd_epyc_rome = create_device_type(
        netbox, "EPYC ROME", "epyc-rome", 1.0, manufacturer_amd
    )
    # Create Device - Standalone
    device_standalone = create_device(
        netbox,
        "example.orthos2.test",
        manufacturer_amd,
        device_type_amd_epyc_rome,
        device_role_server,
        site_orthos2,
    )
    netbox.patch_device(
        device_standalone.get("id", -1), {"custom_fields": {"arch": "x86_64"}}
    )
    # Create MAC address
    mac_address_normal = create_mac_address(netbox, "00:00:5E:00:53:01")
    mac_address_dualstack = create_mac_address(netbox, "00:00:5E:00:53:02")
    mac_address_ipv4 = create_mac_address(netbox, "00:00:5E:00:53:03")
    mac_address_ipv6 = create_mac_address(netbox, "00:00:5E:00:53:04")
    mac_address_mgmt = create_mac_address(netbox, "00:00:5E:00:53:05")
    # Create Interface - With MAC and IP (v4 & v6)
    interface_dualstack = create_interface(
        netbox, "example.orthos2.test", "eth3-dualstack"
    )
    assign_mac_address_to_interface(netbox, mac_address_dualstack, interface_dualstack)
    # Create Interface - With MAC and IP (v4)
    interface_ipv4 = create_interface(netbox, "example.orthos2.test", "eth4-ipv4")
    assign_mac_address_to_interface(netbox, mac_address_ipv4, interface_ipv4)
    # Create Interface - With MAC and IP (v6)
    interface_ipv6 = create_interface(netbox, "example.orthos2.test", "eth5-ipv6")
    assign_mac_address_to_interface(netbox, mac_address_ipv6, interface_ipv6)
    # Create Interface - With MAC
    interface_normal = create_interface(netbox, "example.orthos2.test", "eth0")
    assign_mac_address_to_interface(netbox, mac_address_normal, interface_normal)
    # Create Interface - Empty
    interface_empty = create_interface(netbox, "example.orthos2.test", "eth1-empty")
    # Create Interface - Mgmt
    interface_mgmt = create_interface(
        netbox, "example.orthos2.test", "eth2-mgmt", mgmt_only=True
    )
    try:
        netbox.patch_interface(
            interface_mgmt.get("id", -1),
            {"custom_fields": {"fence_agent": "ipmilanplus"}},
        )
    except requests.exceptions.RequestException:
        pass
    assign_mac_address_to_interface(netbox, mac_address_mgmt, interface_mgmt)
    # Assign IP Addresses to interfaces
    assign_ip_address_to_interface(netbox, ip_address_v4_primary, interface_normal)
    assign_ip_address_to_interface(netbox, ip_address_v6_primary, interface_normal)
    assign_ip_address_to_interface(netbox, ip_address_v4_oob, interface_mgmt)
    assign_ip_address_to_interface(netbox, ip_address_v6_oob, interface_mgmt)
    # Mark IP Address as Primary for Device and Mgmt
    netbox.patch_device(
        device_standalone.get("id", -1),
        {
            "primary_ip4": ip_address_v4_primary.get("id"),
            "primary_ip6": ip_address_v6_primary.get("id"),
            "oob_ip": ip_address_v4_oob.get("id"),
        },
    )
    # Create Device - For Cluster
    device_kvm_host = create_device(
        netbox,
        "example-kvm.orthos2.test",
        manufacturer_amd,
        device_type_amd_epyc_rome,
        device_role_server,
        site_orthos2,
    )
    # Create Cluster Type
    cluster_type_kvm_host = netbox.post_cluster_type(
        {
            "name": "KVM Host",
            "slug": "kvm-host",
            "description": "KVM Clusters that are single-host.",
        }
    )
    # Create Cluster (single device)
    cluster_kvm_host = netbox.post_cluster(
        {
            "name": "example-kvm.orthos2.test",
            "type": {
                "name": cluster_type_kvm_host.get("name"),
                "slug": cluster_type_kvm_host.get("slug"),
            },
            "scope_type": "dcim.site",
            "scope_id": site_orthos2.get("id"),
        }
    )
    # Create Virtual Machines [1-3] - For Cluster
    virtual_machine_1 = netbox.post_virtual_machine(
        {
            "name": "example-kvm-1.orthos2.test",
            "site": site_orthos2.get("id"),
            "cluster": cluster_kvm_host.get("id"),
        }
    )
    virtual_machine_2 = netbox.post_virtual_machine(
        {
            "name": "example-kvm-2.orthos2.test",
            "site": site_orthos2.get("id"),
            "cluster": cluster_kvm_host.get("id"),
        }
    )
    virtual_machine_3 = netbox.post_virtual_machine(
        {
            "name": "example-kvm-3.orthos2.test",
            "site": site_orthos2.get("id"),
            "cluster": cluster_kvm_host.get("id"),
        }
    )
    # Create Cobbler Device
    device_cobbler = create_device(
        netbox,
        "cobbler.orthos2.test",
        manufacturer_amd,
        device_type_amd_epyc_rome,
        device_role_server,
        site_orthos2,
    )
    # Create 2x PowerHMC Device
    # Create PPC64LE LPAR Device
    # Create PPC64LE PowerVM
    # Create S390 Chassis Device
    # Create S390 LPAR
    # Create S390 zVM


main()
