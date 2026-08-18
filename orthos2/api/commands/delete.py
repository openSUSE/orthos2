import json
import logging
from typing import Any, Dict, List, Union

from django.contrib.auth.models import AnonymousUser
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
    DeleteMachineAPIForm,
    DeleteManufacturerAPIForm,
    DeletePlatformAPIForm,
    DeleteRemotePowerAPIForm,
    DeleteRemotePowerDeviceAPIForm,
    DeleteSerialConsoleAPIForm,
)
from orthos2.api.serializers.misc import (
    AuthRequiredSerializer,
    ErrorMessage,
    InputSerializer,
)
from orthos2.data.models import (
    Machine,
    Manufacturer,
    NetworkInterface,
    Platform,
    RemotePowerDevice,
)
from orthos2.utils.misc import format_cli_form_errors

logger = logging.getLogger("api")


class Delete:
    MACHINE = "machine"
    SERIALCONSOLE = "serialconsole"
    REMOTEPOWER = "remotepower"
    REMOTEPOWERDEVICE = "remotepowerdevice"
    MANUFACTURER = "manufacturer"
    PLATFORM = "platform"

    as_list = [
        MACHINE,
        SERIALCONSOLE,
        REMOTEPOWER,
        REMOTEPOWERDEVICE,
        MANUFACTURER,
        PLATFORM,
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
             platform           : Delete a platform (superusers only).

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

        elif item == Delete.PLATFORM:
            if sub_arguments:
                return ErrorMessage(
                    "Invalid number of arguments for 'platform'!"
                ).as_json

            return redirect(reverse("api:platform_delete"))

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


class DeletePlatformCommand(BaseAPIView):

    METHOD = "POST"
    URL = "/platform/delete"
    URL_POST = "/platform/delete"
    ARGUMENTS = (["name"],)

    HELP_SHORT = "Deletes a platform from the database."
    HELP = """Deletes a platform from the database (superusers only).

    Usage:
        DELETE platform <name>
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^platform/delete",
                DeletePlatformCommand.as_view(),
                name="platform_delete",
            ),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return form for deleting a platform."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        form = DeletePlatformAPIForm()

        input = InputSerializer(form.as_dict(), self.URL_POST, form.get_order())
        return input.as_json

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Delete platform."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        form = DeletePlatformAPIForm(data)

        if form.is_valid():
            try:
                cleaned_data = form.cleaned_data

                platform = Platform.objects.get(name__iexact=cleaned_data["name"])

                result = platform.delete()

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
