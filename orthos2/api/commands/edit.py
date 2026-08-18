"""
Command classes for editing existing database objects via the API.
"""

import json
import logging
from typing import Any, List, Union

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
    ArchitectureAPIForm,
    DeviceTypeAPIForm,
    ManufacturerAPIForm,
    SerialConsoleTypeAPIForm,
    ServerConfigAPIForm,
    SingleTaskAPIForm,
    SystemAPIForm,
)
from orthos2.api.serializers.misc import (
    AuthRequiredSerializer,
    ErrorMessage,
    InputSerializer,
    Message,
)
from orthos2.data.models import (
    Architecture,
    DeviceType,
    Manufacturer,
    SerialConsoleType,
    ServerConfig,
    System,
)
from orthos2.taskmanager.models import SingleTask
from orthos2.utils.misc import format_cli_form_errors

logger = logging.getLogger("api")


class Edit:
    MANUFACTURER = "manufacturer"
    DEVICETYPE = "devicetype"
    SERIALCONSOLETYPE = "serialconsoletype"
    SYSTEM = "system"
    ARCHITECTURE = "architecture"
    SERVERCONFIG = "serverconfig"

    as_list = [
        MANUFACTURER,
        DEVICETYPE,
        SERIALCONSOLETYPE,
        SYSTEM,
        ARCHITECTURE,
        SERVERCONFIG,
    ]


class EditCommand(BaseAPIView):

    METHOD = "GET"
    URL = "/edit"
    ARGUMENTS = (["args*"],)

    HELP_SHORT = "Edits information in the database."
    HELP = """Edits items in the database. All information will be queried interactively.

    Usage:
        EDIT <item> [args*]

    Arguments:
        item - Specify the item which should be edited. Items are:

                manufacturer <id>      : Edit a manufacturer (superusers only).
                devicetype <id>        : Edit a device type (superusers only).
                serialconsoletype <id> : Edit a serial console type
                                         (superusers only).
                system <id>            : Edit a system (superusers only).
                architecture <id>      : Edit an architecture (superusers only).
                serverconfig <id>      : Edit a server configuration entry
                                         (superusers only).

    Example:
        EDIT manufacturer 1
        EDIT devicetype 1
        EDIT serialconsoletype 1
        EDIT system 1
        EDIT architecture 1
        EDIT serverconfig 1
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(r"^edit$", EditCommand.as_view(), name="edit"),
        ]

    @staticmethod
    def get_tabcompletion() -> List[str]:
        return Edit.as_list

    def get(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> Union[JsonResponse, HttpResponsePermanentRedirect, HttpResponseRedirect]:
        """Dispatcher for the 'edit' command."""
        arguments = request.GET.get("args", None)

        if arguments:
            arguments = arguments.split()  # type: ignore
            item = arguments[0].lower()
            sub_arguments = arguments[1:]
        else:
            return ErrorMessage("Item is missing!").as_json

        if item == Edit.MANUFACTURER:
            if len(sub_arguments) != 1:
                return ErrorMessage(
                    "Invalid number of arguments for 'manufacturer'!"
                ).as_json

            return redirect(
                "{}?id={}".format(reverse("api:manufacturer_edit"), sub_arguments[0])
            )

        elif item == Edit.DEVICETYPE:
            if len(sub_arguments) != 1:
                return ErrorMessage(
                    "Invalid number of arguments for 'devicetype'!"
                ).as_json

            return redirect(
                "{}?id={}".format(reverse("api:devicetype_edit"), sub_arguments[0])
            )

        elif item == Edit.SERIALCONSOLETYPE:
            if len(sub_arguments) != 1:
                return ErrorMessage(
                    "Invalid number of arguments for 'serialconsoletype'!"
                ).as_json

            return redirect(
                "{}?id={}".format(
                    reverse("api:serialconsoletype_edit"), sub_arguments[0]
                )
            )

        elif item == Edit.SYSTEM:
            if len(sub_arguments) != 1:
                return ErrorMessage("Invalid number of arguments for 'system'!").as_json

            return redirect(
                "{}?id={}".format(reverse("api:system_edit"), sub_arguments[0])
            )

        elif item == Edit.ARCHITECTURE:
            if len(sub_arguments) != 1:
                return ErrorMessage(
                    "Invalid number of arguments for 'architecture'!"
                ).as_json

            return redirect(
                "{}?id={}".format(reverse("api:architecture_edit"), sub_arguments[0])
            )

        elif item == Edit.SERVERCONFIG:
            if len(sub_arguments) != 1:
                return ErrorMessage(
                    "Invalid number of arguments for 'serverconfig'!"
                ).as_json

            return redirect(
                "{}?id={}".format(reverse("api:serverconfig_edit"), sub_arguments[0])
            )

        return ErrorMessage("Unknown item '{}'!".format(item)).as_json


class EditManufacturerCommand(BaseAPIView):

    METHOD = "POST"
    URL = "/manufacturer/edit"
    URL_POST = "/manufacturer/edit"
    ARGUMENTS = (["id", "name"],)

    HELP_SHORT = "Edits a manufacturer in the database."
    HELP = """Edits a manufacturer in the database (superusers only).

    Usage:
        EDIT manufacturer <id>
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^manufacturer/edit",
                EditManufacturerCommand.as_view(),
                name="manufacturer_edit",
            ),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return form for editing a manufacturer."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        manufacturer_id = request.GET.get("id")
        try:
            manufacturer = Manufacturer.objects.get(pk=manufacturer_id)  # type: ignore[misc]
        except (Manufacturer.DoesNotExist, ValueError, TypeError):
            return ErrorMessage(
                "Manufacturer with id '{}' does not exist!".format(manufacturer_id)
            ).as_json

        form = ManufacturerAPIForm(instance=manufacturer)
        fields = form.as_dict()
        fields["id"] = {
            "type": "INTEGER",
            "prompt": "ID",
            "initial": manufacturer.pk,
            "required": True,
        }

        input = InputSerializer(fields, self.URL_POST, ["id"] + form.get_order())
        return input.as_json

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Edit manufacturer."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        manufacturer_id = data.get("id")
        try:
            manufacturer = Manufacturer.objects.get(pk=manufacturer_id)
        except (Manufacturer.DoesNotExist, ValueError, TypeError):
            return ErrorMessage(
                "Manufacturer with id '{}' does not exist!".format(manufacturer_id)
            ).as_json

        form = ManufacturerAPIForm(data, instance=manufacturer)

        if form.is_valid():
            try:
                form.save()
            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

            return Message("Ok.").as_json

        return ErrorMessage(
            "\n{}".format(format_cli_form_errors(form))  # type: ignore[arg-type]
        ).as_json


class EditDeviceTypeCommand(BaseAPIView):

    METHOD = "POST"
    URL = "/devicetype/edit"
    URL_POST = "/devicetype/edit"
    ARGUMENTS = (["id", "name", "manufacturer", "is_cartridge", "description"],)

    HELP_SHORT = "Edits a device type in the database."
    HELP = """Edits a device type in the database (superusers only).

    Usage:
        EDIT devicetype <id>
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^devicetype/edit",
                EditDeviceTypeCommand.as_view(),
                name="devicetype_edit",
            ),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return form for editing a device type."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        devicetype_id = request.GET.get("id")
        try:
            devicetype = DeviceType.objects.get(pk=devicetype_id)  # type: ignore[misc]
        except (DeviceType.DoesNotExist, ValueError, TypeError):
            return ErrorMessage(
                "Device Type with id '{}' does not exist!".format(devicetype_id)
            ).as_json

        form = DeviceTypeAPIForm(instance=devicetype)
        fields = form.as_dict()
        fields["id"] = {
            "type": "INTEGER",
            "prompt": "ID",
            "initial": devicetype.pk,
            "required": True,
        }

        input = InputSerializer(fields, self.URL_POST, ["id"] + form.get_order())
        return input.as_json

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Edit device type."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        devicetype_id = data.get("id")
        try:
            devicetype = DeviceType.objects.get(pk=devicetype_id)
        except (DeviceType.DoesNotExist, ValueError, TypeError):
            return ErrorMessage(
                "Device Type with id '{}' does not exist!".format(devicetype_id)
            ).as_json

        form = DeviceTypeAPIForm(data, instance=devicetype)

        if form.is_valid():
            try:
                form.save()
            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

            return Message("Ok.").as_json

        return ErrorMessage(
            "\n{}".format(format_cli_form_errors(form))  # type: ignore[arg-type]
        ).as_json


class EditSerialConsoleTypeCommand(BaseAPIView):

    METHOD = "POST"
    URL = "/serialconsoletype/edit"
    URL_POST = "/serialconsoletype/edit"
    ARGUMENTS = (["id", "name", "command", "comment", "has_ipmi_sol"],)

    HELP_SHORT = "Edits a serial console type in the database."
    HELP = """Edits a serial console type in the database (superusers only).

    Usage:
        EDIT serialconsoletype <id>
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^serialconsoletype/edit",
                EditSerialConsoleTypeCommand.as_view(),
                name="serialconsoletype_edit",
            ),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return form for editing a serial console type."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        serialconsoletype_id = request.GET.get("id")
        try:
            serialconsoletype = SerialConsoleType.objects.get(pk=serialconsoletype_id)  # type: ignore[misc]
        except (SerialConsoleType.DoesNotExist, ValueError, TypeError):
            return ErrorMessage(
                "Serial console type with id '{}' does not exist!".format(
                    serialconsoletype_id
                )
            ).as_json

        form = SerialConsoleTypeAPIForm(instance=serialconsoletype)
        fields = form.as_dict()
        fields["id"] = {
            "type": "INTEGER",
            "prompt": "ID",
            "initial": serialconsoletype.pk,
            "required": True,
        }

        input = InputSerializer(fields, self.URL_POST, ["id"] + form.get_order())
        return input.as_json

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Edit serial console type."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        serialconsoletype_id = data.get("id")
        try:
            serialconsoletype = SerialConsoleType.objects.get(pk=serialconsoletype_id)
        except (SerialConsoleType.DoesNotExist, ValueError, TypeError):
            return ErrorMessage(
                "Serial console type with id '{}' does not exist!".format(
                    serialconsoletype_id
                )
            ).as_json

        form = SerialConsoleTypeAPIForm(data, instance=serialconsoletype)

        if form.is_valid():
            try:
                form.save()
            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

            return Message("Ok.").as_json

        return ErrorMessage(
            "\n{}".format(format_cli_form_errors(form))  # type: ignore[arg-type]
        ).as_json


class EditSystemCommand(BaseAPIView):

    METHOD = "POST"
    URL = "/system/edit"
    URL_POST = "/system/edit"
    ARGUMENTS = (
        ["id", "name", "virtual", "allowBMC", "allowHypervisor", "administrative"],
    )

    HELP_SHORT = "Edits a system in the database."
    HELP = """Edits a system in the database (superusers only).

    Usage:
        EDIT system <id>
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^system/edit",
                EditSystemCommand.as_view(),
                name="system_edit",
            ),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return form for editing a system."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        system_id = request.GET.get("id")
        try:
            system = System.objects.get(pk=system_id)  # type: ignore[misc]
        except (System.DoesNotExist, ValueError, TypeError):
            return ErrorMessage(
                "System with id '{}' does not exist!".format(system_id)
            ).as_json

        form = SystemAPIForm(instance=system)
        fields = form.as_dict()
        fields["id"] = {
            "type": "INTEGER",
            "prompt": "ID",
            "initial": system.pk,
            "required": True,
        }

        input = InputSerializer(fields, self.URL_POST, ["id"] + form.get_order())
        return input.as_json

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Edit system."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        system_id = data.get("id")
        try:
            system = System.objects.get(pk=system_id)
        except (System.DoesNotExist, ValueError, TypeError):
            return ErrorMessage(
                "System with id '{}' does not exist!".format(system_id)
            ).as_json

        form = SystemAPIForm(data, instance=system)

        if form.is_valid():
            try:
                form.save()
            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

            return Message("Ok.").as_json

        return ErrorMessage(
            "\n{}".format(format_cli_form_errors(form))  # type: ignore[arg-type]
        ).as_json


class EditArchitectureCommand(BaseAPIView):

    METHOD = "POST"
    URL = "/architecture/edit"
    URL_POST = "/architecture/edit"
    ARGUMENTS = (["id", "name", "dhcp_filename", "contact_email", "default_profile"],)

    HELP_SHORT = "Edits an architecture in the database."
    HELP = """Edits an architecture in the database (superusers only).

    Usage:
        EDIT architecture <id>
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^architecture/edit",
                EditArchitectureCommand.as_view(),
                name="architecture_edit",
            ),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return form for editing an architecture."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        architecture_id = request.GET.get("id")
        try:
            architecture = Architecture.objects.get(pk=architecture_id)  # type: ignore[misc]
        except (Architecture.DoesNotExist, ValueError, TypeError):
            return ErrorMessage(
                "Architecture with id '{}' does not exist!".format(architecture_id)
            ).as_json

        form = ArchitectureAPIForm(instance=architecture)
        fields = form.as_dict()
        fields["id"] = {
            "type": "INTEGER",
            "prompt": "ID",
            "initial": architecture.pk,
            "required": True,
        }

        input = InputSerializer(fields, self.URL_POST, ["id"] + form.get_order())
        return input.as_json

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Edit architecture."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        architecture_id = data.get("id")
        try:
            architecture = Architecture.objects.get(pk=architecture_id)
        except (Architecture.DoesNotExist, ValueError, TypeError):
            return ErrorMessage(
                "Architecture with id '{}' does not exist!".format(architecture_id)
            ).as_json

        form = ArchitectureAPIForm(data, instance=architecture)

        if form.is_valid():
            try:
                form.save()
            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

            return Message("Ok.").as_json

        return ErrorMessage(
            "\n{}".format(format_cli_form_errors(form))  # type: ignore[arg-type]
        ).as_json


class EditServerConfigCommand(BaseAPIView):

    METHOD = "POST"
    URL = "/serverconfig/edit"
    URL_POST = "/serverconfig/edit"
    ARGUMENTS = (["id", "key", "value"],)

    HELP_SHORT = "Edits a server configuration entry in the database."
    HELP = """Edits a server configuration entry in the database (superusers only).

    Usage:
        EDIT serverconfig <id>
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^serverconfig/edit",
                EditServerConfigCommand.as_view(),
                name="serverconfig_edit",
            ),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return form for editing a server configuration entry."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        serverconfig_id = request.GET.get("id")
        try:
            serverconfig = ServerConfig.objects.get(pk=serverconfig_id)  # type: ignore[misc]
        except (ServerConfig.DoesNotExist, ValueError, TypeError):
            return ErrorMessage(
                "Server configuration entry with id '{}' does not exist!".format(
                    serverconfig_id
                )
            ).as_json

        form = ServerConfigAPIForm(instance=serverconfig)
        fields = form.as_dict()
        fields["id"] = {
            "type": "INTEGER",
            "prompt": "ID",
            "initial": serverconfig.pk,
            "required": True,
        }

        input = InputSerializer(fields, self.URL_POST, ["id"] + form.get_order())
        return input.as_json

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Edit server configuration entry."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        serverconfig_id = data.get("id")
        try:
            serverconfig = ServerConfig.objects.get(pk=serverconfig_id)
        except (ServerConfig.DoesNotExist, ValueError, TypeError):
            return ErrorMessage(
                "Server configuration entry with id '{}' does not exist!".format(
                    serverconfig_id
                )
            ).as_json

        form = ServerConfigAPIForm(data, instance=serverconfig)

        if form.is_valid():
            try:
                form.save()
            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

            return Message("Ok.").as_json

        return ErrorMessage(
            "\n{}".format(format_cli_form_errors(form))  # type: ignore[arg-type]
        ).as_json


class EditSingleTaskCommand(BaseAPIView):

    METHOD = "POST"
    URL = "/singletask/edit"
    URL_POST = "/singletask/edit"
    ARGUMENTS = (["id", "name", "module", "arguments", "priority"],)

    HELP_SHORT = "Edits a single task in the database."
    HELP = """Edits a single task in the database (superusers only).

    Usage:
        EDIT singletask <id>
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^singletask/edit",
                EditSingleTaskCommand.as_view(),
                name="singletask_edit",
            ),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return form for editing a single task."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        singletask_id = request.GET.get("id")
        try:
            singletask = SingleTask.objects.get(pk=singletask_id)  # type: ignore[misc]
        except (SingleTask.DoesNotExist, ValueError, TypeError):
            return ErrorMessage(
                "Single task with id '{}' does not exist!".format(singletask_id)
            ).as_json

        form = SingleTaskAPIForm(instance=singletask)
        fields = form.as_dict()
        fields["id"] = {
            "type": "INTEGER",
            "prompt": "ID",
            "initial": singletask.pk,
            "required": True,
        }

        input = InputSerializer(fields, self.URL_POST, ["id"] + form.get_order())
        return input.as_json

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Edit single task."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        singletask_id = data.get("id")
        try:
            singletask = SingleTask.objects.get(pk=singletask_id)
        except (SingleTask.DoesNotExist, ValueError, TypeError):
            return ErrorMessage(
                "Single task with id '{}' does not exist!".format(singletask_id)
            ).as_json

        form = SingleTaskAPIForm(data, instance=singletask)

        if form.is_valid():
            try:
                form.save()
            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

            return Message("Ok.").as_json

        return ErrorMessage(
            "\n{}".format(format_cli_form_errors(form))  # type: ignore[arg-type]
        ).as_json
