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
from orthos2.api.serializers.architecture import ArchitectureSerializer
from orthos2.api.serializers.dailytask import DailyTaskSerializer
from orthos2.api.serializers.devicetype import DeviceTypeSerializer
from orthos2.api.serializers.domainarchitecture import DomainArchitectureSerializer
from orthos2.api.serializers.enclosure import EnclosureSerializer
from orthos2.api.serializers.machine import MachineSerializer
from orthos2.api.serializers.manufacturer import ManufacturerSerializer
from orthos2.api.serializers.misc import (
    AuthRequiredSerializer,
    ErrorMessage,
    Serializer,
)
from orthos2.api.serializers.remotepowerdevice import RemotePowerDeviceSerializer
from orthos2.api.serializers.remotepowertype import RemotePowerTypeSerializer
from orthos2.api.serializers.serialconsoletype import SerialConsoleTypeSerializer
from orthos2.api.serializers.singletask import SingleTaskSerializer
from orthos2.api.serializers.system import SystemSerializer
from orthos2.data.models import (
    Architecture,
    DeviceType,
    DomainAdmin,
    Machine,
    Manufacturer,
    RemotePowerDevice,
    RemotePowerType,
    SerialConsoleType,
    System,
)
from orthos2.data.models.enclosure import Enclosure
from orthos2.taskmanager.models import DailyTask, SingleTask


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


class SerialConsoleTypeInfoCommand(BaseAPIView):

    METHOD = "GET"
    URL = "/serialconsoletype"
    ARGUMENTS = (["name"],)

    HELP_SHORT = "Retrieve information about a serial console type."
    HELP = """Command to get information about a serial console type.

Usage:
    INFO serialconsoletype <name>

Arguments:
    name - Name of the serial console type. If omitted, all serial console
           types are listed.

Example:
    INFO serialconsoletype Telnet
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^serialconsoletype$",
                SerialConsoleTypeInfoCommand.as_view(),
                name="serialconsoletype",
            ),
        ]

    @staticmethod
    def get_tabcompletion() -> List[str]:
        return list(SerialConsoleType.objects.all().values_list("name", flat=True))

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return serial console type information."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        name = request.GET.get("name", "")

        try:
            if name:
                serialconsoletype = SerialConsoleType.objects.get(name__iexact=name)
                serialized_serialconsoletype = SerialConsoleTypeSerializer(
                    serialconsoletype
                )
                response = {
                    "header": {
                        "type": "INFO",
                        "order": ["id", "name", "command", "comment", "has_ipmi_sol"],
                    },
                    "data": serialized_serialconsoletype.data_info,
                }
            else:
                serialconsoletypes = SerialConsoleType.objects.all()
                serialized_serialconsoletypes = SerialConsoleTypeSerializer(
                    serialconsoletypes, many=True
                )
                theader = [{"id": "ID"}, {"name": "Name"}, {"command": "Command"}]
                response = {
                    "header": {"type": "TABLE", "theader": theader},
                    "data": serialized_serialconsoletypes.data,
                }
        except SerialConsoleType.DoesNotExist:
            return ErrorMessage(
                "Serial console type '{}' does not exist!".format(name)
            ).as_json
        except Exception:
            return ErrorMessage(getException()).as_json

        return JsonResponse(response)


class SystemInfoCommand(BaseAPIView):

    METHOD = "GET"
    URL = "/system"
    ARGUMENTS = (["name"],)

    HELP_SHORT = "Retrieve information about a system."
    HELP = """Command to get information about a system.

Usage:
    INFO system <name>

Arguments:
    name - Name of the system. If omitted, all systems are listed.

Example:
    INFO system BareMetal
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(r"^system$", SystemInfoCommand.as_view(), name="system"),
        ]

    @staticmethod
    def get_tabcompletion() -> List[str]:
        return list(System.objects.all().values_list("name", flat=True))

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return system information."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        name = request.GET.get("name", "")

        try:
            if name:
                system = System.objects.get(name__iexact=name)
                serialized_system = SystemSerializer(system)
                response = {
                    "header": {
                        "type": "INFO",
                        "order": [
                            "id",
                            "name",
                            "virtual",
                            "allowBMC",
                            "allowHypervisor",
                            "administrative",
                        ],
                    },
                    "data": serialized_system.data_info,
                }
            else:
                systems = System.objects.all()
                serialized_systems = SystemSerializer(systems, many=True)
                theader = [{"id": "ID"}, {"name": "Name"}, {"virtual": "Virtual"}]
                response = {
                    "header": {"type": "TABLE", "theader": theader},
                    "data": serialized_systems.data,
                }
        except System.DoesNotExist:
            return ErrorMessage("System '{}' does not exist!".format(name)).as_json
        except Exception:
            return ErrorMessage(getException()).as_json

        return JsonResponse(response)


class RemotePowerTypeInfoCommand(BaseAPIView):

    METHOD = "GET"
    URL = "/remotepowertype"
    ARGUMENTS = (["name"],)

    HELP_SHORT = "Retrieve information about a remote power type."
    HELP = """Command to get information about a remote power type.

Usage:
    INFO remotepowertype <name>

Arguments:
    name - Name of the remote power type. If omitted, all remote power types
           are listed.

Example:
    INFO remotepowertype APC
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^remotepowertype$",
                RemotePowerTypeInfoCommand.as_view(),
                name="remotepowertype",
            ),
        ]

    @staticmethod
    def get_tabcompletion() -> List[str]:
        return list(RemotePowerType.objects.all().values_list("name", flat=True))

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return remote power type information."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        name = request.GET.get("name", "")

        try:
            if name:
                remotepowertype = RemotePowerType.objects.get(name__iexact=name)
                serialized_remotepowertype = RemotePowerTypeSerializer(remotepowertype)
                response = {
                    "header": {
                        "type": "INFO",
                        "order": [
                            "id",
                            "name",
                            "device",
                            "username",
                            "identity_file",
                            "architectures",
                            "systems",
                            "use_port",
                            "use_hostname_as_port",
                        ],
                    },
                    "data": serialized_remotepowertype.data_info,
                }
            else:
                remotepowertypes = RemotePowerType.objects.all()
                serialized_remotepowertypes = RemotePowerTypeSerializer(
                    remotepowertypes, many=True
                )
                theader = [{"id": "ID"}, {"name": "Name"}, {"device": "Device"}]
                response = {
                    "header": {"type": "TABLE", "theader": theader},
                    "data": serialized_remotepowertypes.data,
                }
        except RemotePowerType.DoesNotExist:
            return ErrorMessage(
                "Remote power type '{}' does not exist!".format(name)
            ).as_json
        except Exception:
            return ErrorMessage(getException()).as_json

        return JsonResponse(response)


class ArchitectureInfoCommand(BaseAPIView):

    METHOD = "GET"
    URL = "/architecture"
    ARGUMENTS = (["name"],)

    HELP_SHORT = "Retrieve information about an architecture."
    HELP = """Command to get information about an architecture.

Usage:
    INFO architecture <name>

Arguments:
    name - Name of the architecture. If omitted, all architectures are
           listed.

Example:
    INFO architecture x86_64
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^architecture$",
                ArchitectureInfoCommand.as_view(),
                name="architecture",
            ),
        ]

    @staticmethod
    def get_tabcompletion() -> List[str]:
        return list(Architecture.objects.all().values_list("name", flat=True))

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return architecture information."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        name = request.GET.get("name", "")

        try:
            if name:
                architecture = Architecture.objects.get(name__iexact=name)
                serialized_architecture = ArchitectureSerializer(architecture)
                response = {
                    "header": {
                        "type": "INFO",
                        "order": [
                            "id",
                            "name",
                            "dhcp_filename",
                            "contact_email",
                            "default_profile",
                        ],
                    },
                    "data": serialized_architecture.data_info,
                }
            else:
                architectures = Architecture.objects.all()
                serialized_architectures = ArchitectureSerializer(
                    architectures, many=True
                )
                theader = [{"id": "ID"}, {"name": "Name"}]
                response = {
                    "header": {"type": "TABLE", "theader": theader},
                    "data": serialized_architectures.data,
                }
        except Architecture.DoesNotExist:
            return ErrorMessage(
                "Architecture '{}' does not exist!".format(name)
            ).as_json
        except Exception:
            return ErrorMessage(getException()).as_json

        return JsonResponse(response)


class SingleTaskInfoCommand(BaseAPIView):

    METHOD = "GET"
    URL = "/singletask"
    ARGUMENTS = (["id"],)

    HELP_SHORT = "Retrieve information about a single task."
    HELP = """Command to get information about a single task.

Usage:
    INFO singletask <id>

Arguments:
    id - ID of the single task. If omitted, all single tasks are listed.

Example:
    INFO singletask 1
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^singletask$", SingleTaskInfoCommand.as_view(), name="singletask"
            ),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return single task information."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        singletask_id = request.GET.get("id")

        try:
            if singletask_id:
                singletask = SingleTask.objects.get(pk=singletask_id)
                serialized_singletask = SingleTaskSerializer(singletask)
                response = {
                    "header": {
                        "type": "INFO",
                        "order": [
                            "id",
                            "name",
                            "module",
                            "arguments",
                            "priority",
                            "hash",
                            "running",
                            "created",
                        ],
                    },
                    "data": serialized_singletask.data_info,
                }
            else:
                singletasks = SingleTask.objects.all()
                serialized_singletasks = SingleTaskSerializer(singletasks, many=True)
                theader = [{"id": "ID"}, {"name": "Name"}, {"running": "Running"}]
                response = {
                    "header": {"type": "TABLE", "theader": theader},
                    "data": serialized_singletasks.data,
                }
        except (SingleTask.DoesNotExist, ValueError, TypeError):
            return ErrorMessage(
                "Single task with id '{}' does not exist!".format(singletask_id)
            ).as_json
        except Exception:
            return ErrorMessage(getException()).as_json

        return JsonResponse(response)


class DailyTaskInfoCommand(BaseAPIView):

    METHOD = "GET"
    URL = "/dailytask"
    ARGUMENTS = (["id"],)

    HELP_SHORT = "Retrieve information about a daily task."
    HELP = """Command to get information about a daily task.

Usage:
    INFO dailytask <id>

Arguments:
    id - ID of the daily task. If omitted, all daily tasks are listed.

Example:
    INFO dailytask 1
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(r"^dailytask$", DailyTaskInfoCommand.as_view(), name="dailytask"),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return daily task information."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        dailytask_id = request.GET.get("id")

        try:
            if dailytask_id:
                dailytask = DailyTask.objects.get(pk=dailytask_id)
                serialized_dailytask = DailyTaskSerializer(dailytask)
                response = {
                    "header": {
                        "type": "INFO",
                        "order": [
                            "id",
                            "name",
                            "module",
                            "arguments",
                            "priority",
                            "enabled",
                            "executed_at",
                            "hash",
                            "running",
                            "created",
                        ],
                    },
                    "data": serialized_dailytask.data_info,
                }
            else:
                dailytasks = DailyTask.objects.all()
                serialized_dailytasks = DailyTaskSerializer(dailytasks, many=True)
                theader = [
                    {"id": "ID"},
                    {"name": "Name"},
                    {"enabled": "Enabled"},
                    {"running": "Running"},
                ]
                response = {
                    "header": {"type": "TABLE", "theader": theader},
                    "data": serialized_dailytasks.data,
                }
        except (DailyTask.DoesNotExist, ValueError, TypeError):
            return ErrorMessage(
                "Daily task with id '{}' does not exist!".format(dailytask_id)
            ).as_json
        except Exception:
            return ErrorMessage(getException()).as_json

        return JsonResponse(response)


class DomainArchitectureInfoCommand(BaseAPIView):

    METHOD = "GET"
    URL = "/domainarchitecture"
    ARGUMENTS = (["domain", "arch"],)

    HELP_SHORT = "Retrieve information about a domain's supported architectures."
    HELP = """Command to get information about a domain's supported architectures.

Usage:
    INFO domainarchitecture <domain> <arch>

Arguments:
    domain - Name of the domain.
    arch   - Name of the architecture. If omitted (along with domain), all
             entries are listed.

Example:
    INFO domainarchitecture orthos2.test x86_64
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^domainarchitecture$",
                DomainArchitectureInfoCommand.as_view(),
                name="domainarchitecture",
            ),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return domain architecture information."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        domain = request.GET.get("domain", "")
        arch = request.GET.get("arch", "")

        try:
            if domain and arch:
                domainarchitecture = DomainAdmin.objects.get(
                    domain__name__iexact=domain, arch__name__iexact=arch
                )
                serialized_domainarchitecture = DomainArchitectureSerializer(
                    domainarchitecture
                )
                response = {
                    "header": {
                        "type": "INFO",
                        "order": ["id", "domain", "arch", "contact_email"],
                    },
                    "data": serialized_domainarchitecture.data_info,
                }
            else:
                domainarchitectures = DomainAdmin.objects.all()
                serialized_domainarchitectures = DomainArchitectureSerializer(
                    domainarchitectures, many=True
                )
                theader = [
                    {"id": "ID"},
                    {"domain": "Domain"},
                    {"arch": "Architecture"},
                ]
                response = {
                    "header": {"type": "TABLE", "theader": theader},
                    "data": serialized_domainarchitectures.data,
                }
        except DomainAdmin.DoesNotExist:
            return ErrorMessage(
                "No supported architecture entry for domain '{}' and "
                "architecture '{}'!".format(domain, arch)
            ).as_json
        except Exception:
            return ErrorMessage(getException()).as_json

        return JsonResponse(response)
