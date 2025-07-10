import logging
import re
from typing import Any, Dict, List, Optional, Union

from django.db import models

from orthos2.data.models import Component

logger = logging.getLogger("models")


class PCIDevice(Component):

    # Annotate to allow type checking of autofield
    id: int

    slot: "models.TextField[Optional[str], Optional[str]]" = models.TextField(
        null=True,
        default=None,
    )

    vendor_id: "models.TextField[Optional[str], Optional[str]]" = models.TextField(
        null=True,
        default=None,
    )

    vendor: "models.TextField[Optional[str], Optional[str]]" = models.TextField(
        null=True,
        default=None,
    )

    device_id: "models.TextField[Optional[str], Optional[str]]" = models.TextField(
        null=True,
        default=None,
    )

    device: "models.TextField[Optional[str], Optional[str]]" = models.TextField(
        null=True,
        default=None,
    )

    class_id: "models.TextField[Optional[str], Optional[str]]" = models.TextField(
        null=True,
        default=None,
    )

    classname: "models.TextField[Optional[str], Optional[str]]" = models.TextField(
        null=True,
        default=None,
    )

    subvendor_id: "models.TextField[Optional[str], Optional[str]]" = models.TextField(
        null=True,
        default=None,
    )

    subvendor: "models.TextField[Optional[str], Optional[str]]" = models.TextField(
        null=True,
        default=None,
    )

    subdevice_id: "models.TextField[Optional[str], Optional[str]]" = models.TextField(
        null=True,
        default=None,
    )

    subdevice: "models.TextField[Optional[str], Optional[str]]" = models.TextField(
        null=True,
        default=None,
    )

    revision: "models.TextField[Optional[str], Optional[str]]" = models.TextField(
        null=True,
        default=None,
    )

    drivermodule: "models.TextField[Optional[str], Optional[str]]" = models.TextField(
        null=True,
        default=None,
    )

    @staticmethod
    def from_lspci_mmnv(text: Union[str, List[str]]) -> "PCIDevice":
        """Create a new `PCIDevice` object from the `lspci -mmnv` output."""
        if not isinstance(text, list):
            text = text.splitlines()

        dev = PCIDevice()

        for line in text:
            if line.startswith("Slot:"):
                dev.slot = line.split("\t")[1].strip()

            elif line.startswith("Class:"):
                # hack: some versions print 'Class:\tClass xxxx'
                clazz = line.split("\t")[1].strip()
                if clazz.startswith("Class "):
                    clazz = clazz[6:]
                dev.class_id = clazz

            elif line.startswith("Vendor:"):
                dev.vendor_id = line.split("\t")[1].strip()

            elif line.startswith("Device:"):
                id = line.split("\t")[1].strip()
                # SLES9 SP4 'lspci' does have 'Slot'
                if id.find(":") > 0:
                    dev.slot = id
                else:
                    dev.device_id = id

            elif line.startswith("SVendor:"):
                dev.subvendor_id = line.split("\t")[1].strip()

            elif line.startswith("SDevice:"):
                dev.subdevice_id = line.split("\t")[1].strip()

            elif line.startswith("Rev:"):
                dev.revision = line.split("\t")[1].strip()

        dev.lookup_missing_names()

        return dev

    def lookup_missing_names(self) -> None:
        """Lookup of missing names in the PCI database of the system."""
        if not self.vendor and self.vendor_id:
            self.vendor = PCIDatabase().get_vendor_from_id(self.vendor_id)

        if not self.device and self.device_id:
            self.device = PCIDatabase().get_device_from_id(
                self.vendor_id, self.device_id
            )

        if not self.classname and self.class_id:
            self.classname = PCIDatabase().get_class_from_id(self.class_id)

        if not self.subvendor and self.subvendor_id:
            self.subvendor = PCIDatabase().get_vendor_from_id(self.subvendor_id)

        if not self.subdevice and self.subdevice_id:
            self.subdevice = PCIDatabase().get_sdevice_from_id(
                self.vendor_id, self.device_id, self.subvendor_id, self.subdevice_id
            )

    def output(self) -> str:
        """
        Convert the PCI device to a long string (more than one line).

        This is for debugging.
        """
        output = ""
        output += "{:<10}: {}\n".format("Slot", self.slot)
        output += "{:<10}: {} [{}]\n".format("Class", self.classname, self.class_id)
        output += "{:<10}: {} [{}]\n".format("Vendor", self.vendor, self.vendor_id)
        output += "{:<10}: {} [{}]\n".format("Device", self.device, self.device_id)
        output += "{:<10}: {} [{}]\n".format(
            "SVendor", self.subvendor, self.subvendor_id
        )
        output += "{:<10}: {} [{}]\n".format(
            "SDevice", self.subdevice, self.subdevice_id
        )
        output += "{:<10}: {}\n".format("Rev", self.revision)
        output += "{:<10}: {}\n".format("Driver", self.drivermodule)

        return output

    def __str__(self) -> str:
        return self.machine.fqdn  # type: ignore

    def __hash__(self) -> int:
        return super().__hash__()

    def __eq__(self, obj: Any) -> bool:
        """
        Compare two PCI devices.

        Two PCI devices are equal if the IDs of the PCI devices are the same. See also `neq()`.
        """
        return (
            type(self) is type(obj)
            and self.device_id == obj.device_id
            and self.vendor_id == obj.vendor_id
            and self.subvendor_id == obj.subvendor_id
            and self.subdevice_id == obj.subdevice_id
        )

    def __neq__(self, obj: Any) -> bool:
        """
        Compare two PCI devices.

        Two PCI devices are not equal if one of the IDs of the PCI devices are not the same.
        See also `eq()`.
        """
        return not self.__eq__(obj)


class PCIDatabase(object):
    """
    Python singleton for the PCI database.

    The database is read on the first access of `PCIDatabase`.
    """

    PCIIDS_FILE = "/usr/share/pci.ids"

    class PCIDatabaseImpl:
        """Singleton implementation that represents the PCI database."""

        def __init__(self) -> None:
            """Initialise the PCIDatabase."""
            self._vendors: Dict[str, str] = {}  # key: vendorid
            self._devices: Dict[str, str] = {}  # key: vendorid:deviceid
            self.sdevices: Dict[
                str, str
            ] = {}  # key: vendorid:deviceid:svendorid:sdeviceid
            self.classes: Dict[str, str] = {}  # key: class
            self.parse_pci_ids(PCIDatabase.PCIIDS_FILE)

        def get_vendor_from_id(self, vendorid: str) -> Optional[str]:
            """Return the vendor for a given ID."""
            vendorid = vendorid.lower()
            if vendorid in self._vendors.keys():
                return self._vendors[vendorid]
            else:
                return None

        def get_device_from_id(self, vendorid: str, deviceid: str) -> Optional[str]:
            """Return the device for given IDs `vendorid` and `deviceid`."""
            vendordeviceid = (vendorid + ":" + deviceid).lower()
            if vendordeviceid in self._devices.keys():
                return self._devices[vendordeviceid]
            else:
                return None

        def get_class_from_id(self, classid: str) -> Optional[str]:
            """Return the class for a given ID."""
            classid = classid.lower()
            if classid in self.classes.keys():
                return self.classes[classid]
            else:
                return None

        def get_sdevice_from_id(
            self, vendorid: str, deviceid: str, svendorid: str, sdeviceid: str
        ) -> Optional[str]:
            """Return the subdevice name for a given ID."""
            key = "{}:{}:{}:{}".format(
                vendorid.lower(), deviceid.lower(), svendorid.lower(), sdeviceid.lower()
            )
            if key in self.sdevices.keys():
                return self.sdevices[key]
            else:
                return None

        def parse_pci_ids(self, filename: str) -> None:
            """
            Parse the `PCIIDS_FILE` file.

            When an error occurs, the function doesn't throw that error but it silently ignores it.
            Of course the error gets logged.
            """
            try:
                f = open(filename, "r")

                current_vendorid = None
                current_deviceid = None
                current_topclassid = None
                current_topclassname = None
                linecount = 0
                for line in f.readlines():
                    linecount += 1

                    # skip comments
                    if not line or line[0] == "#":
                        continue

                    # new vendors
                    match = re.match(r"^([0-9a-fA-F]{4})  (.*)", line)
                    if match:
                        current_vendorid = match.group(1).lower()
                        vendorname = match.group(2)
                        self._vendors[current_vendorid] = vendorname
                        continue

                    # devices
                    match = re.match(r"^\t([0-9a-fA-F]{4})  (.*)", line)
                    if match:
                        current_deviceid = match.group(1).lower()
                        devicename = match.group(2)

                        # add to the list
                        if not current_vendorid:
                            logger.warning(
                                "pci.ids format invalid at line %s", linecount
                            )
                            continue
                        vendordeviceid = "{}:{}".format(
                            current_vendorid, current_deviceid
                        )
                        self._devices[vendordeviceid] = devicename
                        continue

                    # subvendors
                    match = re.match(
                        r"^\t\t([0-9a-fA-F]{4}) ([0-9a-fA-F]{4})  (.*)", line
                    )
                    if match:
                        svendorid = match.group(1).lower()
                        sdeviceid = match.group(2)
                        sdevicename = match.group(3)

                        if not current_vendorid or not current_deviceid:
                            logger.warning(
                                "pci.ids format invalid at line %s", linecount
                            )
                            continue

                        key = "{}:{}:{}:{}".format(
                            current_vendorid, current_deviceid, svendorid, sdeviceid
                        )
                        self.sdevices[key] = sdevicename
                        continue

                    # top classes
                    match = re.match(r"^C ([0-9a-fA-F]{2})  (.*)", line)
                    if match:
                        current_topclassid = match.group(1)
                        current_topclassname = match.group(2)
                        continue

                    # rest of classes
                    if current_topclassid:
                        match = re.match(r"\t([0-9a-fA-F]{2})  (.*)", line)
                        if match:
                            restclassid = match.group(1)
                            restclassname = match.group(2)
                            classid = current_topclassid + restclassid
                            classname = "{}: {}".format(
                                current_topclassname, restclassname
                            )

                            self.classes[classid.lower()] = classname
                            continue

                f.close()
            except IOError as e:
                logger.warning("Unable to read pciids file: %s", str(e))
                logger.exception(e)
            logger.debug("Reading '%s' finished", filename)

    # storage for the instance reference
    __instance = None

    def __init__(self) -> None:
        """Create singleton instance."""
        if PCIDatabase.__instance is None:
            PCIDatabase.__instance = PCIDatabase.PCIDatabaseImpl()

        self.__dict__["_Singleton__instance"] = PCIDatabase.__instance

    def __getattr__(self, attr: str) -> Any:
        """Delegate access to implementation."""
        return getattr(self.__instance, attr)

    def __setattr__(self, attr: str, value: Any) -> None:
        """Delegate access to implementation."""
        return setattr(self.__instance, attr, value)
