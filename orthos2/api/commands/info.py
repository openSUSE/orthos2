from typing import Any, List, Union

from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import URLPattern, re_path
from rest_framework.request import Request

from orthos2.api.commands.base import (
    BaseAPIView,
    get_enclosure,
    get_machine,
    get_remotepowerdevice,
    getException,
)
from orthos2.api.serializers.devicetype import DeviceTypeSerializer
from orthos2.api.serializers.enclosure import EnclosureSerializer
from orthos2.api.serializers.machine import MachineSerializer
from orthos2.api.serializers.manufacturer import ManufacturerSerializer
from orthos2.api.serializers.misc import (
    AuthRequiredSerializer,
    ErrorMessage,
    Serializer,
)
from orthos2.api.serializers.remotepowerdevice import RemotePowerDeviceSerializer
from orthos2.data.models import DeviceType, Machine, Manufacturer, RemotePowerDevice
from orthos2.data.models.enclosure import Enclosure


class InfoCommand(BaseAPIView):

    METHOD = "GET"
    URL = "/machine"
    ARGUMENTS = (["fqdn"],)

    HELP_SHORT = "Retrieve information about a machine."
    HELP = """Command to get information about a machine.

Usage:
    INFO <fqdn>

Arguments:
    fqdn - FQDN or hostname of the machine.

Example:
    INFO foo.domain.tld
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(r"^machine$", InfoCommand.as_view(), name="machine"),
        ]

    @staticmethod
    def get_tabcompletion() -> List[str]:
        return list(Machine.api.all().values_list("fqdn", flat=True))

    def get(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> Union[JsonResponse, HttpResponseRedirect]:
        """Return machine information."""
        fqdn = request.GET.get("fqdn", "")
        response = {}

        try:
            result = get_machine(fqdn, redirect_to="api:machine", data=request.GET)
            if isinstance(result, Serializer):
                return result.as_json
            elif isinstance(result, HttpResponseRedirect):
                return result
            machine = result

            serialzed_machine = MachineSerializer(machine)

            order = [
                "fqdn",
                "id",
                "architecture",
                "ipv4",
                "ipv6",
                "serial_number",
                "product_code",
                "comment",
                "nda",
                None,
                "system",
                "enclosure",
                "group",
                None,
                "location_room",
                "location_rack",
                "location_rack_position",
                None,
                "reserved_by",
                "reserved_reason",
                "reserved_at",
                "reserved_until",
                None,
                "status_ipv4",
                "status_ipv6",
                "status_ssh",
                "status_login",
                None,
                "cpu_model",
                "cpu_id",
                "cpu_physical",
                "cpu_cores",
                "cpu_threads",
                "cpu_flags",
                "ram_amount",
                None,
                "serial_type",
                "serial_cscreen_server",
                "serial_console_server",
                "serial_port",
                "serial_command",
                "serial_comment",
                "serial_baud_rate",
                "serial_kernel_device",
                "serial_kernel_device_num",
                None,
                "power_type",
                "power_host",
                "power_port",
                "power_device",
                "power_comment",
                None,
                "bmc_fqdn",
                "bmc_mac",
                "bmc_username",
                "bmc_password",
                [
                    "installations",
                    [
                        "distribution",
                        "active",
                        "partition",
                        "architecture",
                        "kernelversion",
                    ],
                ],
                [
                    "networkinterfaces",
                    [
                        "mac_address",
                        "name",
                        "ethernet_type",
                        "driver_module",
                        "primary",
                    ],
                ],
                ["annotations", ["text", "reporter", "created"]],
            ]

            response["header"] = {"type": "INFO", "order": order}
            response["data"] = serialzed_machine.data_info  # type: ignore
        except Exception:
            return ErrorMessage(getException()).as_json

        return JsonResponse(response)


class EnclosureInfoCommand(BaseAPIView):
    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(r"^enclosure$", EnclosureInfoCommand.as_view(), name="enclosure"),
        ]

    @staticmethod
    def get_tabcompletion() -> List[str]:
        return list(Enclosure.api.all().values_list("name", flat=True))

    def get(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> Union[JsonResponse, HttpResponseRedirect]:
        """Return machine information."""
        name = request.GET.get("name", "")
        response = {}

        try:
            result = get_enclosure(name, redirect_to="api:enclosure", data=request.GET)
            if isinstance(result, Serializer):
                return result.as_json
            elif isinstance(result, HttpResponseRedirect):
                return result
            enclosure = result

            serialzed_enclosure = EnclosureSerializer(enclosure)

            order = [
                "name",
                "id",
                "description",
                "netbox_id",
                "device_type",
                "netbox_last_fetch_attempt",
                "location_site",
                "location_room",
                "location_rack",
                "location_rack_position",
            ]

            response["header"] = {"type": "INFO", "order": order}
            response["data"] = serialzed_enclosure.data_info  # type: ignore
        except Exception:
            return ErrorMessage(getException()).as_json

        return JsonResponse(response)


class RemotePowerDeviceInfoCommand(BaseAPIView):
    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^remotepowerdevice$",
                RemotePowerDeviceInfoCommand.as_view(),
                name="remotepowerdevice",
            ),
        ]

    @staticmethod
    def get_tabcompletion() -> List[str]:
        return list(RemotePowerDevice.objects.all().values_list("fqdn", flat=True))

    def get(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> Union[JsonResponse, HttpResponseRedirect]:
        """Return remote power device information."""
        fqdn = request.GET.get("fqdn", "")
        response = {}

        try:
            result = get_remotepowerdevice(
                fqdn, redirect_to="api:remotepowerdevice", data=request.GET
            )
            if isinstance(result, Serializer):
                return result.as_json
            elif isinstance(result, HttpResponseRedirect):
                return result
            remotepowerdevice = result

            serialzed_enclosure = RemotePowerDeviceSerializer(remotepowerdevice)

            order = [
                "fqdn",
                "id",
                "username",
                "mac",
                "url",
                "netbox_id",
                "netbox_last_fetch_attempt",
            ]

            response["header"] = {"type": "INFO", "order": order}
            response["data"] = serialzed_enclosure.data_info  # type: ignore
        except Exception:
            return ErrorMessage(getException()).as_json

        return JsonResponse(response)


class ManufacturerInfoCommand(BaseAPIView):

    METHOD = "GET"
    URL = "/manufacturer"
    ARGUMENTS = (["name"],)

    HELP_SHORT = "Retrieve information about a manufacturer."
    HELP = """Command to get information about a manufacturer.

Usage:
    INFO manufacturer <name>

Arguments:
    name - Name of the manufacturer. If omitted, all manufacturers are listed.

Example:
    INFO manufacturer Dell
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^manufacturer$",
                ManufacturerInfoCommand.as_view(),
                name="manufacturer",
            ),
        ]

    @staticmethod
    def get_tabcompletion() -> List[str]:
        return list(Manufacturer.objects.all().values_list("name", flat=True))

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return manufacturer information."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        name = request.GET.get("name", "")

        try:
            if name:
                manufacturer = Manufacturer.objects.get(name__iexact=name)
                serialized_manufacturer = ManufacturerSerializer(manufacturer)
                response = {
                    "header": {"type": "INFO", "order": ["id", "name"]},
                    "data": serialized_manufacturer.data_info,
                }
            else:
                manufacturers = Manufacturer.objects.all()
                serialized_manufacturers = ManufacturerSerializer(
                    manufacturers, many=True
                )
                theader = [{"id": "ID"}, {"name": "Name"}]
                response = {
                    "header": {"type": "TABLE", "theader": theader},
                    "data": serialized_manufacturers.data,
                }
        except Manufacturer.DoesNotExist:
            return ErrorMessage(
                "Manufacturer '{}' does not exist!".format(name)
            ).as_json
        except Exception:
            return ErrorMessage(getException()).as_json

        return JsonResponse(response)


class DeviceTypeInfoCommand(BaseAPIView):

    METHOD = "GET"
    URL = "/devicetype"
    ARGUMENTS = (["name"],)

    HELP_SHORT = "Retrieve information about a device type."
    HELP = """Command to get information about a device type.

Usage:
    INFO devicetype <name>

Arguments:
    name - Name of the device type. If omitted, all device types are listed.

Example:
    INFO devicetype PowerEdge
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^devicetype$", DeviceTypeInfoCommand.as_view(), name="devicetype"
            ),
        ]

    @staticmethod
    def get_tabcompletion() -> List[str]:
        return list(DeviceType.objects.all().values_list("name", flat=True))

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return device type information."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        name = request.GET.get("name", "")

        try:
            if name:
                devicetype = DeviceType.objects.get(name__iexact=name)
                serialized_devicetype = DeviceTypeSerializer(devicetype)
                response = {
                    "header": {
                        "type": "INFO",
                        "order": [
                            "id",
                            "name",
                            "manufacturer",
                            "is_cartridge",
                            "description",
                        ],
                    },
                    "data": serialized_devicetype.data_info,
                }
            else:
                devicetypes = DeviceType.objects.all()
                serialized_devicetypes = DeviceTypeSerializer(devicetypes, many=True)
                theader = [
                    {"id": "ID"},
                    {"name": "Name"},
                    {"manufacturer": "Manufacturer"},
                ]
                response = {
                    "header": {"type": "TABLE", "theader": theader},
                    "data": serialized_devicetypes.data,
                }
        except DeviceType.DoesNotExist:
            return ErrorMessage("Device Type '{}' does not exist!".format(name)).as_json
        except Exception:
            return ErrorMessage(getException()).as_json

        return JsonResponse(response)
