import json
import logging
from typing import Any, Dict, List, Union

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from django.http import (
    HttpResponsePermanentRedirect,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import redirect  # type: ignore
from django.urls import URLPattern, re_path, reverse  # type: ignore
from rest_framework.request import Request

from orthos2.api.commands.base import BaseAPIView
from orthos2.api.forms import (
    DeleteArchitectureAPIForm,
    DeleteBMCAPIForm,
    DeleteDailyTaskAPIForm,
    DeleteDeviceTypeAPIForm,
    DeleteDomainAPIForm,
    DeleteDomainArchitectureAPIForm,
    DeleteEnclosureAPIForm,
    DeleteMachineAPIForm,
    DeleteManufacturerAPIForm,
    DeleteRemotePowerAPIForm,
    DeleteRemotePowerDeviceAPIForm,
    DeleteRemotePowerTypeAPIForm,
    DeleteSerialConsoleAPIForm,
    DeleteSerialConsoleTypeAPIForm,
    DeleteServerConfigAPIForm,
    DeleteSingleTaskAPIForm,
    DeleteSystemAPIForm,
)
from orthos2.api.serializers.misc import (
    AuthRequiredSerializer,
    ErrorMessage,
    InputSerializer,
)
from orthos2.data.models import (
    BMC,
    Architecture,
    DeviceType,
    Domain,
    DomainAdmin,
    Enclosure,
    Machine,
    Manufacturer,
    NetworkInterface,
    RemotePowerDevice,
    RemotePowerType,
    SerialConsoleType,
    ServerConfig,
    System,
)
from orthos2.taskmanager.models import DailyTask, SingleTask
from orthos2.utils.misc import format_cli_form_errors

logger = logging.getLogger("api")


class Delete:
    MACHINE = "machine"
    SERIALCONSOLE = "serialconsole"
    REMOTEPOWER = "remotepower"
    REMOTEPOWERDEVICE = "remotepowerdevice"
    MANUFACTURER = "manufacturer"
    DEVICETYPE = "devicetype"
    SERIALCONSOLETYPE = "serialconsoletype"
    SYSTEM = "system"
    REMOTEPOWERTYPE = "remotepowertype"
    ARCHITECTURE = "architecture"
    SERVERCONFIG = "serverconfig"
    ENCLOSURE = "enclosure"
    DOMAINARCHITECTURE = "domainarchitecture"
    DOMAIN = "domain"
    BMC = "bmc"

    as_list = [
        MACHINE,
        SERIALCONSOLE,
        REMOTEPOWER,
        REMOTEPOWERDEVICE,
        MANUFACTURER,
        DEVICETYPE,
        SERIALCONSOLETYPE,
        SYSTEM,
        REMOTEPOWERTYPE,
        ARCHITECTURE,
        SERVERCONFIG,
        ENCLOSURE,
        DOMAINARCHITECTURE,
        DOMAIN,
        BMC,
    ]


class DeleteCommand(BaseAPIView):

    METHOD = "GET"
    URL = "/delete"
    ARGUMENTS = (["args*"],)

    HELP_SHORT = "Removes information from the database."
    HELP = """Deletes items from the database.

Usage:
    DELETE <item> [args*]

Arguments:
    item - Specify the item which should be deleted. Items are:

             machine            : Delete a machine (superusers only).
             serialconsole      : Delete serial console of a specifc machine
                                    (superusers only).
             remotepower        : Delete remote power of a specifc machine
                                    (superusers only).
             remotepowerdevice  : Delete a remotepower device (superusers only).
             manufacturer       : Delete a manufacturer (superusers only).
             devicetype         : Delete a device type (superusers only).
             serialconsoletype  : Delete a serial console type (superusers only).
             system             : Delete a system (superusers only).
             remotepowertype    : Delete a remote power type (superusers only).
             architecture       : Delete an architecture (superusers only).
             serverconfig       : Delete a server configuration entry
                                    (superusers only).
             enclosure          : Delete an enclosure (superusers only).
             domainarchitecture : Delete a supported architecture entry for a
                                    domain (superusers only).
             domain             : Delete a domain (superusers only).
             bmc                : Delete a BMC (superusers only).

Example:
    DELETE machine
"""

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(r"^delete$", DeleteCommand.as_view(), name="delete"),
        ]

    @staticmethod
    def get_tabcompletion() -> List[str]:
        return Delete.as_list

    def get(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> Union[JsonResponse, HttpResponsePermanentRedirect, HttpResponseRedirect]:
        """Dispatcher for the 'delete' command."""
        arguments = request.GET.get("args", None)

        if arguments:
            arguments = arguments.split()  # type: ignore
            item = arguments[0].lower()
            sub_arguments = arguments[1:]
        else:
            return ErrorMessage("Item is missing!").as_json

        if item == Delete.MACHINE:
            if sub_arguments:
                return ErrorMessage(
                    "Invalid number of arguments for 'machine'!"
                ).as_json

            return redirect(reverse("api:machine_delete"))

        elif item == Delete.SERIALCONSOLE:
            if sub_arguments:
                return ErrorMessage(
                    "Invalid number of arguments for 'serialconsole'!"
                ).as_json

            return redirect(reverse("api:serialconsole_delete"))

        elif item == Delete.REMOTEPOWER:
            if sub_arguments:
                return ErrorMessage(
                    "Invalid number of arguments for 'remotepower'!"
                ).as_json

            return redirect(reverse("api:remotepower_delete"))

        elif item == Delete.REMOTEPOWERDEVICE:
            if sub_arguments:
                return ErrorMessage(
                    "Invalid number of arguments for 'remotepowerdevice'!"
                ).as_json

            return redirect(reverse("api:remotepowerdevice_delete"))

        elif item == Delete.MANUFACTURER:
            if sub_arguments:
                return ErrorMessage(
                    "Invalid number of arguments for 'manufacturer'!"
                ).as_json

            return redirect(reverse("api:manufacturer_delete"))

        elif item == Delete.DEVICETYPE:
            if sub_arguments:
                return ErrorMessage(
                    "Invalid number of arguments for 'devicetype'!"
                ).as_json

            return redirect(reverse("api:devicetype_delete"))

        elif item == Delete.SERIALCONSOLETYPE:
            if sub_arguments:
                return ErrorMessage(
                    "Invalid number of arguments for 'serialconsoletype'!"
                ).as_json

            return redirect(reverse("api:serialconsoletype_delete"))

        elif item == Delete.SYSTEM:
            if sub_arguments:
                return ErrorMessage("Invalid number of arguments for 'system'!").as_json

            return redirect(reverse("api:system_delete"))

        elif item == Delete.REMOTEPOWERTYPE:
            if sub_arguments:
                return ErrorMessage(
                    "Invalid number of arguments for 'remotepowertype'!"
                ).as_json

            return redirect(reverse("api:remotepowertype_delete"))

        elif item == Delete.ARCHITECTURE:
            if sub_arguments:
                return ErrorMessage(
                    "Invalid number of arguments for 'architecture'!"
                ).as_json

            return redirect(reverse("api:architecture_delete"))

        elif item == Delete.SERVERCONFIG:
            if sub_arguments:
                return ErrorMessage(
                    "Invalid number of arguments for 'serverconfig'!"
                ).as_json

            return redirect(reverse("api:serverconfig_delete"))

        elif item == Delete.ENCLOSURE:
            if sub_arguments:
                return ErrorMessage(
                    "Invalid number of arguments for 'enclosure'!"
                ).as_json

            return redirect(reverse("api:enclosure_delete"))

        elif item == Delete.DOMAINARCHITECTURE:
            if sub_arguments:
                return ErrorMessage(
                    "Invalid number of arguments for 'domainarchitecture'!"
                ).as_json

            return redirect(reverse("api:domainarchitecture_delete"))

        elif item == Delete.DOMAIN:
            if sub_arguments:
                return ErrorMessage("Invalid number of arguments for 'domain'!").as_json

            return redirect(reverse("api:domain_delete"))

        elif item == Delete.BMC:
            if sub_arguments:
                return ErrorMessage("Invalid number of arguments for 'bmc'!").as_json

            return redirect(reverse("api:bmc_delete"))

        return ErrorMessage("Unknown item '{}'!".format(item)).as_json


class DeleteMachineCommand(BaseAPIView):

    URL_POST = "/machine/delete"

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^machine/delete",
                DeleteMachineCommand.as_view(),
                name="machine_delete",
            ),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return form for deleting a machine."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        form = DeleteMachineAPIForm()

        input = InputSerializer(form.as_dict(), self.URL_POST, form.get_order())
        return input.as_json

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Delete machine."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        form = DeleteMachineAPIForm(data)

        if form.is_valid():

            try:
                cleaned_data = form.cleaned_data

                machine = Machine.objects.get(fqdn__iexact=cleaned_data["fqdn"])

                if not machine:
                    return ErrorMessage(
                        "Unknown machine '{}'!".format(cleaned_data["fqdn"])
                    ).as_json

                result = machine.delete()

                theader = [
                    {"objects": "Deleted objects"},
                    {"count": "#"},
                ]

                response: Dict[str, Any] = {
                    "header": {"type": "TABLE", "theader": theader},
                    "data": [],
                }
                for key, value in result[1].items():
                    response["data"].append(  # type: ignore
                        {"objects": key.replace("data.", ""), "count": value}
                    )
                return JsonResponse(response)

            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

        return ErrorMessage("\n{}".format(format_cli_form_errors(form))).as_json


class DeleteSerialConsoleCommand(BaseAPIView):

    URL_POST = "/serialconsole/delete"

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^serialconsole/delete",
                DeleteSerialConsoleCommand.as_view(),
                name="serialconsole_delete",
            ),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return form for deleting a serial console."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        form = DeleteSerialConsoleAPIForm()

        input = InputSerializer(form.as_dict(), self.URL_POST, form.get_order())
        return input.as_json

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Delete serial console."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        form = DeleteSerialConsoleAPIForm(data)

        if form.is_valid():

            try:
                cleaned_data = form.cleaned_data

                machine = Machine.objects.get(fqdn__iexact=cleaned_data["fqdn"])

                if not machine.has_serialconsole():
                    return ErrorMessage("Machine has no serial console!").as_json

                result = machine.serialconsole.delete()

                theader = [
                    {"objects": "Deleted objects"},
                    {"count": "#"},
                ]

                response: Dict[str, Any] = {
                    "header": {"type": "TABLE", "theader": theader},
                    "data": [],
                }
                for key, value in result[1].items():
                    response["data"].append(  # type: ignore
                        {"objects": key.replace("data.", ""), "count": value}
                    )
                return JsonResponse(response)

            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

        return ErrorMessage("\n{}".format(format_cli_form_errors(form))).as_json


class DeleteRemotePowerCommand(BaseAPIView):

    URL_POST = "/remotepower/delete"

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^remotepower/delete",
                DeleteRemotePowerCommand.as_view(),
                name="remotepower_delete",
            ),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return form for deleting a remote power."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        form = DeleteRemotePowerAPIForm()

        input = InputSerializer(form.as_dict(), self.URL_POST, form.get_order())
        return input.as_json

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Delete remote power."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        form = DeleteRemotePowerAPIForm(data)

        if form.is_valid():

            try:
                cleaned_data = form.cleaned_data

                machine = Machine.objects.get(fqdn__iexact=cleaned_data["fqdn"])

                if not machine.has_remotepower():
                    return ErrorMessage("Machine has no remote power!").as_json

                result = machine.remotepower.delete()

                theader = [
                    {"objects": "Deleted objects"},
                    {"count": "#"},
                ]

                response: Dict[str, Any] = {
                    "header": {"type": "TABLE", "theader": theader},
                    "data": [],
                }
                for key, value in result[1].items():
                    response["data"].append(  # type: ignore
                        {"objects": key.replace("data.", ""), "count": value}
                    )
                return JsonResponse(response)

            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

        return ErrorMessage("\n{}".format(format_cli_form_errors(form))).as_json


class DeleteRemotePowerDeviceCommand(BaseAPIView):

    URL_POST = "/remotepowerdevice/delete"

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^remotepowerdevice/delete",
                DeleteRemotePowerDeviceCommand.as_view(),
                name="remotepowerdevice_delete",
            ),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return form for deleting a remote power."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        form = DeleteRemotePowerDeviceAPIForm()

        input = InputSerializer(form.as_dict(), self.URL_POST, form.get_order())
        return input.as_json

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Delete remote power."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        form = DeleteRemotePowerDeviceAPIForm(data)

        if form.is_valid():

            try:
                cleaned_data = form.cleaned_data

                device = RemotePowerDevice.objects.get(  # type: ignore
                    fqdn__iexact=cleaned_data["fqdn"]
                )

                result = device.delete()

                theader = [
                    {"objects": "Deleted objects"},
                    {"count": "#"},
                ]

                response: Dict[str, Any] = {
                    "header": {"type": "TABLE", "theader": theader},
                    "data": [],
                }
                for key, value in result[1].items():
                    response["data"].append(  # type: ignore
                        {"objects": key.replace("data.", ""), "count": value}
                    )
                return JsonResponse(response)

            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

        return ErrorMessage("\n{}".format(format_cli_form_errors(form))).as_json


class DeleteNetworkInterfaceCommand(BaseAPIView):
    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^networkinterface/(?P<id>[0-9]+)$",
                DeleteNetworkInterfaceCommand.as_view(),
                name="networkinterface_delete",
            ),
        ]

    def delete(
        self, request: Request, id: int, *args: Any, **kwargs: Any
    ) -> JsonResponse:
        """Delete a network interface by ID."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        try:
            interface = NetworkInterface.objects.get(pk=id)
        except NetworkInterface.DoesNotExist:
            return ErrorMessage(
                "Network interface with id '{}' does not exist!".format(id)
            ).as_json

        if interface.primary:
            return ErrorMessage(
                "The primary network interface cannot be deleted!"
            ).as_json

        try:
            result = interface.delete()

            theader = [
                {"objects": "Deleted objects"},
                {"count": "#"},
            ]

            response: Dict[str, Any] = {
                "header": {"type": "TABLE", "theader": theader},
                "data": [],
            }
            for key, value in result[1].items():
                response["data"].append(  # type: ignore
                    {"objects": key.replace("data.", ""), "count": value}
                )
            return JsonResponse(response)

        except Exception as e:
            logger.exception(e)
            return ErrorMessage("Something went wrong!").as_json


class DeleteManufacturerCommand(BaseAPIView):

    METHOD = "POST"
    URL = "/manufacturer/delete"
    URL_POST = "/manufacturer/delete"
    ARGUMENTS = (["name"],)

    HELP_SHORT = "Deletes a manufacturer from the database."
    HELP = """Deletes a manufacturer from the database (superusers only).

    Usage:
        DELETE manufacturer <name>
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^manufacturer/delete",
                DeleteManufacturerCommand.as_view(),
                name="manufacturer_delete",
            ),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return form for deleting a manufacturer."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        form = DeleteManufacturerAPIForm()

        input = InputSerializer(form.as_dict(), self.URL_POST, form.get_order())
        return input.as_json

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Delete manufacturer."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        form = DeleteManufacturerAPIForm(data)

        if form.is_valid():
            try:
                cleaned_data = form.cleaned_data

                manufacturer = Manufacturer.objects.get(
                    name__iexact=cleaned_data["name"]
                )

                result = manufacturer.delete()

                theader = [
                    {"objects": "Deleted objects"},
                    {"count": "#"},
                ]

                response: Dict[str, Any] = {
                    "header": {"type": "TABLE", "theader": theader},
                    "data": [],
                }
                for key, value in result[1].items():
                    response["data"].append(  # type: ignore
                        {"objects": key.replace("data.", ""), "count": value}
                    )
                return JsonResponse(response)

            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

        return ErrorMessage("\n{}".format(format_cli_form_errors(form))).as_json


class DeleteDeviceTypeCommand(BaseAPIView):

    METHOD = "POST"
    URL = "/devicetype/delete"
    URL_POST = "/devicetype/delete"
    ARGUMENTS = (["name"],)

    HELP_SHORT = "Deletes a device type from the database."
    HELP = """Deletes a device type from the database (superusers only).

    Usage:
        DELETE devicetype <name>
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^devicetype/delete",
                DeleteDeviceTypeCommand.as_view(),
                name="devicetype_delete",
            ),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return form for deleting a device type."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        form = DeleteDeviceTypeAPIForm()

        input = InputSerializer(form.as_dict(), self.URL_POST, form.get_order())
        return input.as_json

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Delete device type."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        form = DeleteDeviceTypeAPIForm(data)

        if form.is_valid():
            try:
                cleaned_data = form.cleaned_data

                device_type = DeviceType.objects.get(name__iexact=cleaned_data["name"])

                result = device_type.delete()

                theader = [
                    {"objects": "Deleted objects"},
                    {"count": "#"},
                ]

                response: Dict[str, Any] = {
                    "header": {"type": "TABLE", "theader": theader},
                    "data": [],
                }
                for key, value in result[1].items():
                    response["data"].append(  # type: ignore
                        {"objects": key.replace("data.", ""), "count": value}
                    )
                return JsonResponse(response)

            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

        return ErrorMessage("\n{}".format(format_cli_form_errors(form))).as_json


class DeleteSerialConsoleTypeCommand(BaseAPIView):

    METHOD = "POST"
    URL = "/serialconsoletype/delete"
    URL_POST = "/serialconsoletype/delete"
    ARGUMENTS = (["name"],)

    HELP_SHORT = "Deletes a serial console type from the database."
    HELP = """Deletes a serial console type from the database (superusers only).

    Usage:
        DELETE serialconsoletype <name>
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^serialconsoletype/delete",
                DeleteSerialConsoleTypeCommand.as_view(),
                name="serialconsoletype_delete",
            ),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return form for deleting a serial console type."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        form = DeleteSerialConsoleTypeAPIForm()

        input = InputSerializer(form.as_dict(), self.URL_POST, form.get_order())
        return input.as_json

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Delete serial console type."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        form = DeleteSerialConsoleTypeAPIForm(data)

        if form.is_valid():
            try:
                cleaned_data = form.cleaned_data

                serialconsoletype = SerialConsoleType.objects.get(
                    name__iexact=cleaned_data["name"]
                )

                result = serialconsoletype.delete()

                theader = [
                    {"objects": "Deleted objects"},
                    {"count": "#"},
                ]

                response: Dict[str, Any] = {
                    "header": {"type": "TABLE", "theader": theader},
                    "data": [],
                }
                for key, value in result[1].items():
                    response["data"].append(  # type: ignore
                        {"objects": key.replace("data.", ""), "count": value}
                    )
                return JsonResponse(response)

            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

        return ErrorMessage("\n{}".format(format_cli_form_errors(form))).as_json


class DeleteSystemCommand(BaseAPIView):

    METHOD = "POST"
    URL = "/system/delete"
    URL_POST = "/system/delete"
    ARGUMENTS = (["name"],)

    HELP_SHORT = "Deletes a system from the database."
    HELP = """Deletes a system from the database (superusers only).

    Usage:
        DELETE system <name>
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^system/delete",
                DeleteSystemCommand.as_view(),
                name="system_delete",
            ),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return form for deleting a system."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        form = DeleteSystemAPIForm()

        input = InputSerializer(form.as_dict(), self.URL_POST, form.get_order())
        return input.as_json

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Delete system."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        form = DeleteSystemAPIForm(data)

        if form.is_valid():
            try:
                cleaned_data = form.cleaned_data

                system = System.objects.get(name__iexact=cleaned_data["name"])

                result = system.delete()

                theader = [
                    {"objects": "Deleted objects"},
                    {"count": "#"},
                ]

                response: Dict[str, Any] = {
                    "header": {"type": "TABLE", "theader": theader},
                    "data": [],
                }
                for key, value in result[1].items():
                    response["data"].append(  # type: ignore
                        {"objects": key.replace("data.", ""), "count": value}
                    )
                return JsonResponse(response)

            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

        return ErrorMessage("\n{}".format(format_cli_form_errors(form))).as_json


class DeleteRemotePowerTypeCommand(BaseAPIView):

    METHOD = "POST"
    URL = "/remotepowertype/delete"
    URL_POST = "/remotepowertype/delete"
    ARGUMENTS = (["name"],)

    HELP_SHORT = "Deletes a remote power type from the database."
    HELP = """Deletes a remote power type from the database (superusers only).

    Usage:
        DELETE remotepowertype <name>
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^remotepowertype/delete",
                DeleteRemotePowerTypeCommand.as_view(),
                name="remotepowertype_delete",
            ),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return form for deleting a remote power type."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        form = DeleteRemotePowerTypeAPIForm()

        input = InputSerializer(form.as_dict(), self.URL_POST, form.get_order())
        return input.as_json

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Delete remote power type."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        form = DeleteRemotePowerTypeAPIForm(data)

        if form.is_valid():
            try:
                cleaned_data = form.cleaned_data

                remotepowertype = RemotePowerType.objects.get(
                    name__iexact=cleaned_data["name"]
                )

                result = remotepowertype.delete()

                theader = [
                    {"objects": "Deleted objects"},
                    {"count": "#"},
                ]

                response: Dict[str, Any] = {
                    "header": {"type": "TABLE", "theader": theader},
                    "data": [],
                }
                for key, value in result[1].items():
                    response["data"].append(  # type: ignore
                        {"objects": key.replace("data.", ""), "count": value}
                    )
                return JsonResponse(response)

            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

        return ErrorMessage("\n{}".format(format_cli_form_errors(form))).as_json


class DeleteArchitectureCommand(BaseAPIView):

    METHOD = "POST"
    URL = "/architecture/delete"
    URL_POST = "/architecture/delete"
    ARGUMENTS = (["name"],)

    HELP_SHORT = "Deletes an architecture from the database."
    HELP = """Deletes an architecture from the database (superusers only).

    Usage:
        DELETE architecture <name>
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^architecture/delete",
                DeleteArchitectureCommand.as_view(),
                name="architecture_delete",
            ),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return form for deleting an architecture."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        form = DeleteArchitectureAPIForm()

        input = InputSerializer(form.as_dict(), self.URL_POST, form.get_order())
        return input.as_json

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Delete architecture."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        form = DeleteArchitectureAPIForm(data)

        if form.is_valid():
            try:
                cleaned_data = form.cleaned_data

                architecture = Architecture.objects.get(
                    name__iexact=cleaned_data["name"]
                )

                result = architecture.delete()

                theader = [
                    {"objects": "Deleted objects"},
                    {"count": "#"},
                ]

                response: Dict[str, Any] = {
                    "header": {"type": "TABLE", "theader": theader},
                    "data": [],
                }
                for key, value in result[1].items():
                    response["data"].append(  # type: ignore
                        {"objects": key.replace("data.", ""), "count": value}
                    )
                return JsonResponse(response)

            except ValidationError as e:
                return ErrorMessage(str(e.message)).as_json
            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

        return ErrorMessage("\n{}".format(format_cli_form_errors(form))).as_json


class DeleteServerConfigCommand(BaseAPIView):

    METHOD = "POST"
    URL = "/serverconfig/delete"
    URL_POST = "/serverconfig/delete"
    ARGUMENTS = (["key"],)

    HELP_SHORT = "Deletes a server configuration entry from the database."
    HELP = """Deletes a server configuration entry from the database (superusers only).

    Usage:
        DELETE serverconfig <key>
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^serverconfig/delete",
                DeleteServerConfigCommand.as_view(),
                name="serverconfig_delete",
            ),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return form for deleting a server configuration entry."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        form = DeleteServerConfigAPIForm()

        input = InputSerializer(form.as_dict(), self.URL_POST, form.get_order())
        return input.as_json

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Delete server configuration entry."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        form = DeleteServerConfigAPIForm(data)

        if form.is_valid():
            try:
                cleaned_data = form.cleaned_data

                serverconfig = ServerConfig.objects.get(key__iexact=cleaned_data["key"])

                result = serverconfig.delete()

                theader = [
                    {"objects": "Deleted objects"},
                    {"count": "#"},
                ]

                response: Dict[str, Any] = {
                    "header": {"type": "TABLE", "theader": theader},
                    "data": [],
                }
                for key, value in result[1].items():
                    response["data"].append(  # type: ignore
                        {"objects": key.replace("data.", ""), "count": value}
                    )
                return JsonResponse(response)

            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

        return ErrorMessage("\n{}".format(format_cli_form_errors(form))).as_json


class DeleteDailyTaskCommand(BaseAPIView):

    METHOD = "POST"
    URL = "/dailytask/delete"
    URL_POST = "/dailytask/delete"
    ARGUMENTS = (["id"],)

    HELP_SHORT = "Deletes a daily task from the database."
    HELP = """Deletes a daily task from the database (superusers only).

    Usage:
        DELETE dailytask <id>
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^dailytask/delete",
                DeleteDailyTaskCommand.as_view(),
                name="dailytask_delete",
            ),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return form for deleting a daily task."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        form = DeleteDailyTaskAPIForm()

        input = InputSerializer(form.as_dict(), self.URL_POST, form.get_order())
        return input.as_json

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Delete daily task."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        form = DeleteDailyTaskAPIForm(data)

        if form.is_valid():
            try:
                cleaned_data = form.cleaned_data

                dailytask = DailyTask.objects.get(pk=cleaned_data["id"])

                result = dailytask.delete()

                theader = [
                    {"objects": "Deleted objects"},
                    {"count": "#"},
                ]

                response: Dict[str, Any] = {
                    "header": {"type": "TABLE", "theader": theader},
                    "data": [],
                }
                for key, value in result[1].items():
                    response["data"].append(  # type: ignore
                        {"objects": key.replace("data.", ""), "count": value}
                    )
                return JsonResponse(response)

            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

        return ErrorMessage("\n{}".format(format_cli_form_errors(form))).as_json


class DeleteSingleTaskCommand(BaseAPIView):

    METHOD = "POST"
    URL = "/singletask/delete"
    URL_POST = "/singletask/delete"
    ARGUMENTS = (["id"],)

    HELP_SHORT = "Deletes a single task from the database."
    HELP = """Deletes a single task from the database (superusers only).

    Usage:
        DELETE singletask <id>
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^singletask/delete",
                DeleteSingleTaskCommand.as_view(),
                name="singletask_delete",
            ),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return form for deleting a single task."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        form = DeleteSingleTaskAPIForm()

        input = InputSerializer(form.as_dict(), self.URL_POST, form.get_order())
        return input.as_json

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Delete single task."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        form = DeleteSingleTaskAPIForm(data)

        if form.is_valid():
            try:
                cleaned_data = form.cleaned_data

                singletask = SingleTask.objects.get(pk=cleaned_data["id"])

                result = singletask.delete()

                theader = [
                    {"objects": "Deleted objects"},
                    {"count": "#"},
                ]

                response: Dict[str, Any] = {
                    "header": {"type": "TABLE", "theader": theader},
                    "data": [],
                }
                for key, value in result[1].items():
                    response["data"].append(  # type: ignore
                        {"objects": key.replace("data.", ""), "count": value}
                    )
                return JsonResponse(response)

            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

        return ErrorMessage("\n{}".format(format_cli_form_errors(form))).as_json


class DeleteEnclosureCommand(BaseAPIView):

    METHOD = "POST"
    URL = "/enclosure/delete"
    URL_POST = "/enclosure/delete"
    ARGUMENTS = (["name"],)

    HELP_SHORT = "Deletes an enclosure from the database."
    HELP = """Deletes an enclosure from the database (superusers only).

    Usage:
        DELETE enclosure <name>
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^enclosure/delete",
                DeleteEnclosureCommand.as_view(),
                name="enclosure_delete",
            ),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return form for deleting an enclosure."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        form = DeleteEnclosureAPIForm()

        input = InputSerializer(form.as_dict(), self.URL_POST, form.get_order())
        return input.as_json

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Delete enclosure."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        form = DeleteEnclosureAPIForm(data)

        if form.is_valid():
            try:
                cleaned_data = form.cleaned_data

                enclosure = Enclosure.objects.get(name__iexact=cleaned_data["name"])

                result = enclosure.delete()

                theader = [
                    {"objects": "Deleted objects"},
                    {"count": "#"},
                ]

                response: Dict[str, Any] = {
                    "header": {"type": "TABLE", "theader": theader},
                    "data": [],
                }
                for key, value in result[1].items():
                    response["data"].append(  # type: ignore
                        {"objects": key.replace("data.", ""), "count": value}
                    )
                return JsonResponse(response)

            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

        return ErrorMessage("\n{}".format(format_cli_form_errors(form))).as_json


class DeleteDomainArchitectureCommand(BaseAPIView):

    METHOD = "POST"
    URL = "/domainarchitecture/delete"
    URL_POST = "/domainarchitecture/delete"
    ARGUMENTS = (["domain", "arch"],)

    HELP_SHORT = "Deletes a supported architecture entry for a domain."
    HELP = """Deletes a supported architecture entry for a domain (superusers only).

    Usage:
        DELETE domainarchitecture <domain> <arch>
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^domainarchitecture/delete",
                DeleteDomainArchitectureCommand.as_view(),
                name="domainarchitecture_delete",
            ),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return form for deleting a supported architecture entry for a domain."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        form = DeleteDomainArchitectureAPIForm()

        input = InputSerializer(form.as_dict(), self.URL_POST, form.get_order())
        return input.as_json

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Delete supported architecture entry for a domain."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        form = DeleteDomainArchitectureAPIForm(data)

        if form.is_valid():
            try:
                cleaned_data = form.cleaned_data

                domainarchitecture = DomainAdmin.objects.get(
                    domain__name__iexact=cleaned_data["domain"],
                    arch__name__iexact=cleaned_data["arch"],
                )

                result = domainarchitecture.delete()

                theader = [
                    {"objects": "Deleted objects"},
                    {"count": "#"},
                ]

                response: Dict[str, Any] = {
                    "header": {"type": "TABLE", "theader": theader},
                    "data": [],
                }
                for key, value in result[1].items():
                    response["data"].append(  # type: ignore
                        {"objects": key.replace("data.", ""), "count": value}
                    )
                return JsonResponse(response)

            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

        return ErrorMessage("\n{}".format(format_cli_form_errors(form))).as_json


class DeleteDomainCommand(BaseAPIView):

    METHOD = "POST"
    URL = "/domain/delete"
    URL_POST = "/domain/delete"
    ARGUMENTS = (["name"],)

    HELP_SHORT = "Deletes a domain from the database."
    HELP = """Deletes a domain from the database (superusers only).

    Usage:
        DELETE domain <name>
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^domain/delete",
                DeleteDomainCommand.as_view(),
                name="domain_delete",
            ),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return form for deleting a domain."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        form = DeleteDomainAPIForm()

        input = InputSerializer(form.as_dict(), self.URL_POST, form.get_order())
        return input.as_json

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Delete domain."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        form = DeleteDomainAPIForm(data)

        if form.is_valid():
            try:
                cleaned_data = form.cleaned_data

                domain = Domain.objects.get(name__iexact=cleaned_data["name"])

                result = domain.delete()

                theader = [
                    {"objects": "Deleted objects"},
                    {"count": "#"},
                ]

                response: Dict[str, Any] = {
                    "header": {"type": "TABLE", "theader": theader},
                    "data": [],
                }
                for key, value in result[1].items():
                    response["data"].append(  # type: ignore
                        {"objects": key.replace("data.", ""), "count": value}
                    )
                return JsonResponse(response)

            except ValidationError as e:
                return ErrorMessage(str(e.message)).as_json
            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

        return ErrorMessage("\n{}".format(format_cli_form_errors(form))).as_json


class DeleteBMCCommand(BaseAPIView):

    METHOD = "POST"
    URL = "/bmc/delete"
    URL_POST = "/bmc/delete"
    ARGUMENTS = (["fqdn"],)

    HELP_SHORT = "Deletes a BMC from the database."
    HELP = """Deletes a BMC from the database (superusers only).

    Usage:
        DELETE bmc <fqdn>
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^bmc/delete",
                DeleteBMCCommand.as_view(),
                name="bmc_delete",
            ),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return form for deleting a BMC."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        form = DeleteBMCAPIForm()

        input = InputSerializer(form.as_dict(), self.URL_POST, form.get_order())
        return input.as_json

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Delete BMC."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        form = DeleteBMCAPIForm(data)

        if form.is_valid():
            try:
                cleaned_data = form.cleaned_data

                bmc = BMC.objects.get(fqdn__iexact=cleaned_data["fqdn"])

                result = bmc.delete()

                theader = [
                    {"objects": "Deleted objects"},
                    {"count": "#"},
                ]

                response: Dict[str, Any] = {
                    "header": {"type": "TABLE", "theader": theader},
                    "data": [],
                }
                for key, value in result[1].items():
                    response["data"].append(  # type: ignore
                        {"objects": key.replace("data.", ""), "count": value}
                    )
                return JsonResponse(response)

            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

        return ErrorMessage("\n{}".format(format_cli_form_errors(form))).as_json
