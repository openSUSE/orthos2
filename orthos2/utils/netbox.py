"""
Utility module that wraps the functionality that is related to Netbox. This is assuming Netbox version 4.
"""

import json
import logging
import urllib
from typing import Any, Dict, List, Literal, Optional

import requests
import urllib3

from orthos2 import settings

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger("utils")


class REST:
    def __init__(self, host: str, token: str):
        self.base_url = "{}/api".format(host)

        # Create HTTP connection pool
        self.s = requests.Session()

        # SSL verification
        self.s.verify = False

        # Define REST Headers
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json; indent=4",
            "Authorization": "Token {0}".format(token),
        }

        self.s.headers.update(headers)

    def uploader(self, data: Dict[str, Any], url: str) -> Dict[str, Any]:
        method = "POST"

        logger.debug("HTTP Request: %s - %s - %s", method, url, data)

        request = requests.Request(method, url, data=json.dumps(data))
        prepared_request = self.s.prepare_request(request)
        r = self.s.send(prepared_request)
        if r.status_code != 201:
            logger.warning(
                f"HTTP Response: %s - %s - %s", r.status_code, r.reason, r.text
            )
        r.raise_for_status()

        return r.json()  # type: ignore

    def patcher(self, data: Dict[str, Any], url: str) -> Dict[str, Any]:
        method = "PATCH"

        logger.debug("HTTP Request: %s - %s - %s", method, url, data)

        request = requests.Request(method, url, data=json.dumps(data))
        prepared_request = self.s.prepare_request(request)
        r = self.s.send(prepared_request)
        if r.status_code != 200:
            logger.warning(
                f"HTTP Response: %s - %s - %s", r.status_code, r.reason, r.text
            )
        r.raise_for_status()

        return r.json()  # type: ignore

    def fetcher(self, url: str) -> Dict[str, Any]:
        method = "GET"

        logger.debug("HTTP Request: %s - %s", method, url)

        request = requests.Request(method, url)
        prepared_request = self.s.prepare_request(request)
        r = self.s.send(prepared_request)

        if r.status_code != 200:
            logger.warning(
                f"HTTP Response: %s - %s - %s", r.status_code, r.reason, r.text
            )
        r.raise_for_status()

        return r.json()  # type: ignore

    def deleter(self, url: str) -> requests.Response:
        method = "DELETE"

        logger.warning("HTTP Request: %s - %s", method, url)

        request = requests.Request(method, url)
        prepared_request = self.s.prepare_request(request)
        r = self.s.send(prepared_request)
        if r.status_code != 204:
            logger.warning(
                f"HTTP Response: %s - %s - %s", r.status_code, r.reason, r.text
            )
        r.raise_for_status()

        return r


class Netbox(REST):
    __object: Optional["Netbox"] = None

    def __init__(self, host: str, token: str):
        super().__init__(host, token)

    @classmethod
    def get_instance(cls):
        if cls.__object is None:
            cls.__object = Netbox(settings.NETBOX_URL, settings.NETBOX_TOKEN)
        return cls.__object

    def fetch_device_roles(self) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/dcim/device-roles/"
        logger.debug(f"Fetching device roles from {url}")
        data = self.fetcher(url)
        results = data["results"]
        url = data["next"]
        while url:
            data = self.fetcher(url)
            for d in data["results"]:
                results.append(d)
                url = data["next"]
        return results  # type: ignore

    def fetch_tenancy_users(self) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/tenancy/contacts/"
        logger.debug(f"Fetching device roles from {url}")
        data = self.fetcher(url)
        results = data["results"]
        url = data["next"]
        while url:
            data = self.fetcher(url)
            for d in data["results"]:
                results.append(d)
                url = data["next"]
        return results  # type: ignore

    def fetch_tenancy_roles(self) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/tenancy/contact-roles/"
        logger.debug(f"Fetching contact roles from {url}")
        data = self.fetcher(url)
        results = data["results"]
        url = data["next"]
        while url:
            data = self.fetcher(url)
            for d in data["results"]:
                results.append(d)
                url = data["next"]
        return results  # type: ignore

    def fetch_interfaces(self) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/dcim/interfaces/"
        logger.debug("Checking MAC address from %s", url)
        data = self.fetcher(url)
        results = data["results"]
        return results  # type: ignore
        url = data["next"]
        while url:
            data = self.fetcher(url)
            for d in data["results"]:
                results.append(d)
                url = data["next"]
        return results

    def fetch_interface(self, id: int) -> Dict[str, Any]:
        url = f"{self.base_url}/dcim/interfaces/{id}/"
        logger.debug("Checking MAC address from %s", url)
        data = self.fetcher(url)
        return data

    def fetch_vm_interface(self, id: int) -> Dict[str, Any]:
        url = f"{self.base_url}/virtualization/interfaces/{id}/"
        logger.debug("Checking MAC address from %s", url)
        data = self.fetcher(url)
        return data

    def fetch_device_type(self, id: int) -> Dict[str, Any]:
        url = f"{self.base_url}/dcim/device-types/{id}/"
        logger.debug("Fetch device data from %s", url)
        data = self.fetcher(url)
        return data

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

    def check_site(self, site: str) -> List[Dict[str, Any]]:
        url = self.base_url + "/dcim/sites/?slug=" + site
        logger.debug(f"Checking site from {url}")
        data = self.fetcher(url)
        return data["results"]

    def check_location(self, loc: str):
        url = f"{self.base_url}/dcim/locations/?slug={loc}"
        logger.debug(f"Checking location from {url}")
        data = self.fetcher(url)
        return data["results"]

    def check_rack(self, loc: str, rack: str):
        url = f"{self.base_url}/dcim/racks/?name={rack}&location={loc}"
        logger.debug(f"Checking rack from {url}")
        data = self.fetcher(url)
        return data["results"]

    def check_ip(self, addr: str):
        url = f"{self.base_url}/ipam/ip-addresses/?address={addr}"
        logger.debug("Checking ip address from %s", url)
        data = self.fetcher(url)
        return data["results"]

    def check_ip_prefix(self, addr: str):
        url = f"{self.base_url}/ipam/prefixes/?contains={addr}"
        logger.debug("Checking ip address from %s", url)
        data = self.fetcher(url)
        return data["results"]

    def check_prefix(self, prefix: str):
        url = f"{self.base_url}/ipam/prefixes/?prefix={prefix}"
        logger.debug("Checking ip address from %s", url)
        data = self.fetcher(url)
        return data["results"]

    def check_ip_by_name(self, fqdn: str):
        url = f"{self.base_url}/ipam/ip-addresses/?q={fqdn}"
        logger.debug("Checking ip address from %s", url)
        data = self.fetcher(url)
        results = data["results"]
        url = data["next"]
        while url:
            data = self.fetcher(url)
            for d in data["results"]:
                results.append(d)
            url = data["next"]
        return results

    def check_ip_by_id(self, id: int):
        url = f"{self.base_url}/ipam/ip-addresses/?device_id={id}"
        logger.debug("Checking ip address from %s", url)
        data = self.fetcher(url)
        if not data["results"]:
            url = f"{self.base_url}/ipam/ip-addresses/?virtual_machine_id={id}"
            logger.debug("Checking ip address from %s", url)
            data = self.fetcher(url)
        return data["results"]

    def check_ip_by_interface(self, id: int):
        url = f"{self.base_url}/ipam/ip-addresses/?interface_id={id}"
        logger.debug("Checking ip address from %s", url)
        data = self.fetcher(url)
        return data["results"]

    def check_ip_by_interface_family(self, id: int, family: Literal[4, 6]):
        url = f"{self.base_url}/ipam/ip-addresses/?interface_id={id}&family={family}"
        logger.debug("Checking ip address from %s", url)
        data = self.fetcher(url)
        return data["results"]

    def check_vlan(self, vid: int):
        url = f"{self.base_url}/ipam/vlans/?vid={vid}"
        logger.debug("Checking vlans from %s", url)
        data = self.fetcher(url)
        return data["results"]

    def check_vlan_group(self, name: str):
        url = f"{self.base_url}/ipam/vlan-groups/?name={name}"
        logger.debug("Checking vlans from %s", url)
        data = self.fetcher(url)
        return data["results"]

    def check_mac_address(self, mac: str):
        url = f"{self.base_url}/dcim/interfaces/?mac_address={mac}"
        logger.debug("Checking MAC address from %s", url)
        data = self.fetcher(url)
        results = data["results"]
        url = f"{self.base_url}/virtualization/interfaces/?mac_address={mac}"
        data = self.fetcher(url)
        for d in data["results"]:
            results.append(d)
        return results

    def check_vm_mac_address(self, mac: str):
        url = f"{self.base_url}/virtualization/interfaces/?mac_address={mac}"
        logger.debug("Checking MAC address from %s", url)
        data = self.fetcher(url)
        return data["results"]

    def check_interface(self, id: int, ifname: str):
        safe_ifname: str = urllib.parse.quote_plus(ifname)  # type: ignore
        url = f"{self.base_url}/dcim/interfaces/?device_id={id}&name={safe_ifname}"
        logger.debug("Checking MAC address from %s", url)
        data = self.fetcher(url)
        return data["results"]

    def check_interface_by_id(self, id: int):
        url = f"{self.base_url}/dcim/interfaces/?device_id={id}"
        return self.__check_interface(url)

    def check_interface_no_mgmt_by_id(self, id: int):
        url = f"{self.base_url}/dcim/interfaces/?device_id={id}&mgmt_only=false"
        return self.__check_interface(url)

    def check_interface_mgmt_by_id(self, id: int):
        url = f"{self.base_url}/dcim/interfaces/?device_id={id}&mgmt_only=true"
        return self.__check_interface(url)

    def __check_interface(self, url: str):
        logger.debug("Checking MAC address from %s", url)
        data = self.fetcher(url)
        results = data["results"]
        url = data["next"]
        while url:
            data = self.fetcher(url)
            for d in data["results"]:
                results.append(d)
            url = data["next"]
        return results

    def check_vm_interface(self, id: int, ifname: str):
        safe_ifname: str = urllib.parse.quote_plus(ifname)  # type: ignore
        url = f"{self.base_url}/virtualization/interfaces/?virtual_machine_id={id}&name={safe_ifname}"
        logger.debug("Checking MAC address from %s", url)
        data = self.fetcher(url)
        return data["results"]

    def check_vm_interface_by_id(self, id: int):
        url = f"{self.base_url}/virtualization/interfaces/?virtual_machine_id={id}"
        logger.debug("Checking MAC address from %s", url)
        data = self.fetcher(url)
        return data["results"]

    def check_power_port(self, id: int, ifname: str):
        safe_ifname: str = urllib.parse.quote_plus(ifname)  # type: ignore
        url = f"{self.base_url}/dcim/power-ports/?device_id={id}&name={safe_ifname}"
        logger.debug("Checking power port from %s", url)
        data = self.fetcher(url)
        return data["results"]

    def check_power_outlet(self, id: int, ifname: str):
        safe_ifname: str = urllib.parse.quote_plus(ifname)  # type: ignore
        url = f"{self.base_url}/dcim/power-outlets/?device_id={id}&name={safe_ifname}"
        logger.debug("Checking power outlet from %s", url)
        data = self.fetcher(url)
        return data["results"]

    def check_console_port(self, id: int, ifname: str):
        safe_ifname: str = urllib.parse.quote_plus(ifname)  # type: ignore
        url = f"{self.base_url}/dcim/console-ports/?device_id={id}&name={safe_ifname}"
        logger.debug("Checking console port from %s", url)
        data = self.fetcher(url)
        return data["results"]

    def check_console_server_port(self, id: int, ifname: str):
        safe_ifname: str = urllib.parse.quote_plus(ifname)  # type: ignore
        url = f"{self.base_url}/dcim/console-server-ports/?device_id={id}&name={safe_ifname}"
        logger.debug("Checking console server port from %s", url)
        data = self.fetcher(url)
        return data["results"]

    def check_orthos_user(self, obj: int):
        url = f"{self.base_url}/tenancy/contact-assignments/?object_id={obj}&role=orthos-user"
        logger.debug("Checking device from %s", url)
        data = self.fetcher(url)
        return data["results"]

    def check_tenancy_user(self, user: str):
        safe_user: str = urllib.parse.quote_plus(user)  # type: ignore
        url = f"{self.base_url}/tenancy/contacts/?email={safe_user}"
        logger.debug("Checking tenancy user from %s", url)
        data = self.fetcher(url)
        if len(data["results"]) > 1:
            logger.warning(f"Duplicate email {user}")
            raise ValueError
        res = None
        if data["results"]:
            res = data["results"][0]
        if not res:
            url = f"{self.base_url}/tenancy/contacts/?cf_alias={safe_user}"
            data = self.fetcher(url)
            if len(data["results"]) > 1:
                logger.warning(f"Duplicate alias {user}")
                raise ValueError
            if data["results"]:
                res = data["results"][0]
        if not res and "@" in user:
            username = user.split("@")[0]
            url = f"{self.base_url}/tenancy/contacts/?cf_ldap_uid={username}"
            data = self.fetcher(url)
            for d in data["results"]:
                if d["custom_fields"]["ldap_uid"] == username:
                    if res:
                        logger.warning(f"Duplicate ldap uid {username}")
                        raise ValueError
                    res = d
        return res

    def check_ldap_user(self, user: str) -> Dict[str, Any]:
        url = f"{self.base_url}/tenancy/contacts/?cf_ldap_uid={user}"
        logger.debug("Checking tenancy user from %s", url)
        data = self.fetcher(url)
        for res in data["results"]:
            if res["custom_fields"]["ldap_uid"] == user:
                return res
        return {}

    def check_tenants(self, tenant: str):
        url = f"{self.base_url}/tenancy/tenants/?q={tenant}"
        logger.debug("Checking tenancy user from %s", url)
        data = self.fetcher(url)
        return data["results"]

    def check_tenancy_assignments(self, obj: int):
        url = f"{self.base_url}/tenancy/contact-assignments/?object_id={obj}"
        logger.debug("Checking device from %s", url)
        data = self.fetcher(url)
        return data["results"]

    def check_contact_assignments(self, obj: int):
        url = f"{self.base_url}/tenancy/contact-assignments/?contact_id={obj}"
        logger.debug("Checking device from %s", url)
        data = self.fetcher(url)
        results = data["results"]
        url = data["next"]
        while url:
            data = self.fetcher(url)
            for d in data["results"]:
                results.append(d)
            url = data["next"]
        return results

    def check_platform(self, plat: str):
        url = f"{self.base_url}/dcim/platforms/?name={plat}"
        data = self.fetcher(url)
        return data["results"]

    def check_manufacturer(self, manuf: str):
        url = f"{self.base_url}/dcim/manufacturers/?slug={manuf}"
        data = self.fetcher(url)
        return data["results"]

    def check_hardware(self, hw: str, manuf_id: int):
        url = f"{self.base_url}/dcim/device-types/?slug={hw}&manufacturer_id={manuf_id}"
        logger.debug(f"Checking hardware from {url}")
        data = self.fetcher(url)
        return data["results"]

    def check_device(self, dev: str):
        url = f"{self.base_url}/dcim/devices/?q={dev}"
        logger.debug(f"Checking device from {url}")
        data = self.fetcher(url)
        results = data["results"]
        url = f"{self.base_url}/virtualization/virtual-machines/?q={dev}"
        logger.debug(f"Checking VM from {url}")
        data = self.fetcher(url)
        for d in data["results"]:
            results.append(d)
        return results

    def check_vm(self, dev: str):
        url = f"{self.base_url}/virtualization/virtual-machines/?name={dev}"
        logger.debug("checking vm from %s", url)
        data = self.fetcher(url)
        return data["results"]

    def check_vmcluster(self, dev: str):
        url = f"{self.base_url}/virtualization/clusters/?name={dev}"
        logger.debug("checking vmcluster from %s", url)
        data = self.fetcher(url)
        return data["results"]

    def check_cname(self, dev: str):
        url = f"{self.base_url}/dcim/devices/?cf_cname={dev}"
        logger.debug("Checking device from %s", url)
        data = self.fetcher(url)
        return data["results"]

    def check_orthos_id(self, id: int):
        url = f"{self.base_url}/dcim/devices/?cf_orthos_id={id}"
        logger.debug(f"Checking device from {url}")
        data = self.fetcher(url)
        return data["results"]

    def check_vm_orthos_id(self, id: int):
        url = f"{self.base_url}/virtualization/virtual-machines/?cf_orthos_id={id}"
        logger.debug(f"Checking device from {url}")
        data = self.fetcher(url)
        return data["results"]

    def check_device_by_rt_id(self, id: int):
        url = f"{self.base_url}/dcim/devices/?cf_rt_object_id={id}"
        logger.debug(f"Checking device from {url}")
        data = self.fetcher(url)
        if data["results"]:
            return data["results"]
        url = f"{self.base_url}/virtualization/virtual-machines/?cf_rt_object_id={id}"
        logger.debug(f"Checking vm from {url}")
        data = self.fetcher(url)
        if data["results"]:
            return data["results"]
        url = f"{self.base_url}/virtualization/clusters/?cf_rt_object_id={id}"
        logger.debug(f"Checking cluster from {url}")
        data = self.fetcher(url)
        if data["results"]:
            return data["results"]
        url = f"{self.base_url}/dcim/modules/?cf_rt_object_id={id}"
        logger.debug(f"Checking module from {url}")
        data = self.fetcher(url)
        if data["results"]:
            return data["results"]
        url = f"{self.base_url}/dcim/virtual-chassis/?cf_rt_object_id={id}"
        logger.debug(f"Checking virtual chassis from {url}")
        data = self.fetcher(url)
        return data["results"]

    def check_device_by_uuid(self, uuid: str):
        url = f"{self.base_url}/dcim/devices/?cf_uuid={uuid}"
        logger.debug(f"Checking device from {url}")
        data = self.fetcher(url)
        if data["results"]:
            return data["results"]
        url = f"{self.base_url}/virtualization/virtual-machines/?cf_uuid={uuid}"
        logger.debug(f"Checking vm from {url}")
        data = self.fetcher(url)
        return data["results"]

    def check_device_by_asset(self, asset: str):
        url = f"{self.base_url}/dcim/devices/?asset_tag={asset}"
        logger.debug(f"Checking device from {url}")
        data = self.fetcher(url)
        results = data["results"]
        url = f"{self.base_url}/virtualization/virtual-machines/?cf_asset_tag={asset}"
        logger.debug(f"Checking vm from {url}")
        data = self.fetcher(url)
        for d in data["results"]:
            results.append(d)
        url = f"{self.base_url}/virtualization/clusters/?cf_asset_tag={asset}"
        logger.debug(f"Checking vmcluster from {url}")
        data = self.fetcher(url)
        for d in data["results"]:
            results.append(d)
        return results

    def check_device_by_location(self, loc: int):
        url = f"{self.base_url}/dcim/devices/?location_id={loc}"
        logger.debug("Checking device from %s", url)
        data = self.fetcher(url)
        results = data["results"]
        url = data["next"]
        while url:
            logger.debug("Fetching more device from %s", url)
            data = self.fetcher(url)
            for d in data["results"]:
                results.append(d)
            url = data["next"]
        return results

    def check_device_by_location_and_tag(self, loc: int, tag: str):
        url = f"{self.base_url}/dcim/devices/?location_id={loc}&tag={tag}"
        logger.warning("Checking device from %s", url)
        data = self.fetcher(url)
        results = data["results"]
        url = data["next"]
        while url:
            logger.warning("Fetching more device from %s", url)
            data = self.fetcher(url)
            for d in data["results"]:
                results.append(d)
                url = data["next"]
        return results

    def check_device_by_tag(self, tag: str):
        url = f"{self.base_url}/dcim/devices/?tag={tag}"
        logger.warning("Checking device from %s", url)
        data = self.fetcher(url)
        results = data["results"]
        url = data["next"]
        while url:
            logger.warning("Fetching more device from %s", url)
            data = self.fetcher(url)
            for d in data["results"]:
                results.append(d)
                url = data["next"]
        return results

    def check_device_by_type(self, type: int):
        url = f"{self.base_url}/dcim/devices/?device_type_id={type}"
        logger.warning("Checking device from %s", url)
        data = self.fetcher(url)
        results = data["results"]
        url = data["next"]
        while url:
            logger.warning("Fetching more device from %s", url)
            data = self.fetcher(url)
            for d in data["results"]:
                results.append(d)
                url = data["next"]
        return results

    def check_cable(self, obj_a: int, obj_b: int):
        url = f"{self.base_url}/dcim/cables/?termination_a_id={obj_a}&termination_b_id={obj_b}"
        logger.debug(f"Fetching cable from {url}")
        data = self.fetcher(url)
        return data["results"]
