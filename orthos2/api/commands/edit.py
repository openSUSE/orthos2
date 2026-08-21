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

from orthos2.api.commands.base import BaseAPIView, get_machine
from orthos2.api.forms import (
    ArchitectureAPIForm,
    BMCAPIForm,
    DailyTaskAPIForm,
    DeviceTypeAPIForm,
    DomainAPIForm,
    DomainArchitectureAPIForm,
    EnclosureAPIForm,
    ManufacturerAPIForm,
    NetworkInterfaceAPIForm,
    RemotePowerAPIForm,
    RemotePowerDeviceAPIForm,
    RemotePowerTypeAPIForm,
    SerialConsoleAPIForm,
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
    Serializer,
)
from orthos2.data.models import (
    BMC,
    Architecture,
    DeviceType,
    Domain,
    DomainAdmin,
    Enclosure,
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


class Edit:
    MANUFACTURER = "manufacturer"
    DEVICETYPE = "devicetype"
    SERIALCONSOLETYPE = "serialconsoletype"
    SYSTEM = "system"
    REMOTEPOWERTYPE = "remotepowertype"
    ARCHITECTURE = "architecture"
    SERVERCONFIG = "serverconfig"
    ENCLOSURE = "enclosure"
    REMOTEPOWERDEVICE = "remotepowerdevice"
    DOMAINARCHITECTURE = "domainarchitecture"
    DOMAIN = "domain"
    NETWORKINTERFACE = "networkinterface"
    SERIALCONSOLE = "serialconsole"
    REMOTEPOWER = "remotepower"
    BMC = "bmc"

    as_list = [
        MANUFACTURER,
        DEVICETYPE,
        SERIALCONSOLETYPE,
        SYSTEM,
        REMOTEPOWERTYPE,
        ARCHITECTURE,
        SERVERCONFIG,
        ENCLOSURE,
        REMOTEPOWERDEVICE,
        DOMAINARCHITECTURE,
        DOMAIN,
        SERIALCONSOLE,
        NETWORKINTERFACE,
        REMOTEPOWER,
        BMC,
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
                remotepowertype <id>   : Edit a remote power type
                                         (superusers only).
                architecture <id>      : Edit an architecture (superusers only).
                serverconfig <id>      : Edit a server configuration entry
                                         (superusers only).
                enclosure <id>         : Edit an enclosure (superusers only).
                remotepowerdevice <id> : Edit a remote power device
                                         (superusers only).
                domainarchitecture <id> : Edit a supported architecture entry
                                         for a domain (superusers only).
                domain <id>            : Edit a domain (superusers only).
                networkinterface <id>  : Edit a network interface
                                         (superusers only).
                serialconsole <fqdn>   : Edit the serial console of a
                                         specific machine (superusers only).
                remotepower <fqdn>     : Edit the remote power of a
                                         specific machine (superusers only).
                bmc <id>               : Edit a BMC (superusers only).

    Example:
        EDIT manufacturer 1
        EDIT devicetype 1
        EDIT serialconsoletype 1
        EDIT system 1
        EDIT remotepowertype 1
        EDIT architecture 1
        EDIT serverconfig 1
        EDIT enclosure 1
        EDIT remotepowerdevice 1
        EDIT domainarchitecture 1
        EDIT domain 1
        EDIT networkinterface 1
        EDIT serialconsole foo.domain.tld
        EDIT remotepower foo.domain.tld
        EDIT bmc 1
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

        elif item == Edit.REMOTEPOWERTYPE:
            if len(sub_arguments) != 1:
                return ErrorMessage(
                    "Invalid number of arguments for 'remotepowertype'!"
                ).as_json

            return redirect(
                "{}?id={}".format(reverse("api:remotepowertype_edit"), sub_arguments[0])
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

        elif item == Edit.ENCLOSURE:
            if len(sub_arguments) != 1:
                return ErrorMessage(
                    "Invalid number of arguments for 'enclosure'!"
                ).as_json

            return redirect(
                "{}?id={}".format(reverse("api:enclosure_edit"), sub_arguments[0])
            )

        elif item == Edit.REMOTEPOWERDEVICE:
            if len(sub_arguments) != 1:
                return ErrorMessage(
                    "Invalid number of arguments for 'remotepowerdevice'!"
                ).as_json

            return redirect(
                "{}?id={}".format(
                    reverse("api:remotepowerdevice_edit"), sub_arguments[0]
                )
            )

        elif item == Edit.DOMAINARCHITECTURE:
            if len(sub_arguments) != 1:
                return ErrorMessage(
                    "Invalid number of arguments for 'domainarchitecture'!"
                ).as_json

            return redirect(
                "{}?id={}".format(
                    reverse("api:domainarchitecture_edit"), sub_arguments[0]
                )
            )

        elif item == Edit.DOMAIN:
            if len(sub_arguments) != 1:
                return ErrorMessage("Invalid number of arguments for 'domain'!").as_json

            return redirect(
                "{}?id={}".format(reverse("api:domain_edit"), sub_arguments[0])
            )

        elif item == Edit.NETWORKINTERFACE:
            if len(sub_arguments) != 1:
                return ErrorMessage(
                    "Invalid number of arguments for 'networkinterface'!"
                ).as_json

            return redirect(
                "{}?id={}".format(
                    reverse("api:networkinterface_edit"), sub_arguments[0]
                )
            )

        elif item == Edit.SERIALCONSOLE:
            if len(sub_arguments) != 1:
                return ErrorMessage(
                    "Invalid number of arguments for 'serialconsole'!"
                ).as_json

            return redirect(
                "{}?fqdn={}".format(
                    reverse("api:serialconsole_edit_get"), sub_arguments[0]
                )
            )

        elif item == Edit.REMOTEPOWER:
            if len(sub_arguments) != 1:
                return ErrorMessage(
                    "Invalid number of arguments for 'remotepower'!"
                ).as_json

            return redirect(
                "{}?fqdn={}".format(
                    reverse("api:remotepower_edit_get"), sub_arguments[0]
                )
            )

        elif item == Edit.BMC:
            if len(sub_arguments) != 1:
                return ErrorMessage("Invalid number of arguments for 'bmc'!").as_json

            return redirect(
                "{}?id={}".format(reverse("api:bmc_edit"), sub_arguments[0])
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


class EditRemotePowerTypeCommand(BaseAPIView):

    METHOD = "POST"
    URL = "/remotepowertype/edit"
    URL_POST = "/remotepowertype/edit"
    ARGUMENTS = (
        [
            "id",
            "name",
            "device",
            "username",
            "password",
            "identity_file",
            "architectures",
            "systems",
            "use_port",
            "use_hostname_as_port",
        ],
    )

    HELP_SHORT = "Edits a remote power type in the database."
    HELP = """Edits a remote power type in the database (superusers only).

    Usage:
        EDIT remotepowertype <id>
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^remotepowertype/edit",
                EditRemotePowerTypeCommand.as_view(),
                name="remotepowertype_edit",
            ),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return form for editing a remote power type."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        remotepowertype_id = request.GET.get("id")
        try:
            remotepowertype = RemotePowerType.objects.get(pk=remotepowertype_id)  # type: ignore[misc]
        except (RemotePowerType.DoesNotExist, ValueError, TypeError):
            return ErrorMessage(
                "Remote power type with id '{}' does not exist!".format(
                    remotepowertype_id
                )
            ).as_json

        form = RemotePowerTypeAPIForm(instance=remotepowertype)
        fields = form.as_dict()
        fields["id"] = {
            "type": "INTEGER",
            "prompt": "ID",
            "initial": remotepowertype.pk,
            "required": True,
        }

        input = InputSerializer(fields, self.URL_POST, ["id"] + form.get_order())
        return input.as_json

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Edit remote power type."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        remotepowertype_id = data.get("id")
        try:
            remotepowertype = RemotePowerType.objects.get(pk=remotepowertype_id)
        except (RemotePowerType.DoesNotExist, ValueError, TypeError):
            return ErrorMessage(
                "Remote power type with id '{}' does not exist!".format(
                    remotepowertype_id
                )
            ).as_json

        form = RemotePowerTypeAPIForm(data, instance=remotepowertype)

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


class EditDailyTaskCommand(BaseAPIView):

    METHOD = "POST"
    URL = "/dailytask/edit"
    URL_POST = "/dailytask/edit"
    ARGUMENTS = (["id", "task", "arguments", "priority", "enabled"],)

    HELP_SHORT = "Edits a daily task in the database."
    HELP = """Edits a daily task in the database (superusers only).

    Usage:
        EDIT dailytask <id>
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^dailytask/edit",
                EditDailyTaskCommand.as_view(),
                name="dailytask_edit",
            ),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return form for editing a daily task."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        dailytask_id = request.GET.get("id")
        try:
            dailytask = DailyTask.objects.get(pk=dailytask_id)  # type: ignore[misc]
        except (DailyTask.DoesNotExist, ValueError, TypeError):
            return ErrorMessage(
                "Daily task with id '{}' does not exist!".format(dailytask_id)
            ).as_json

        form = DailyTaskAPIForm(instance=dailytask)
        fields = form.as_dict()
        fields["id"] = {
            "type": "INTEGER",
            "prompt": "ID",
            "initial": dailytask.pk,
            "required": True,
        }

        input = InputSerializer(fields, self.URL_POST, ["id"] + form.get_order())
        return input.as_json

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Edit daily task."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        dailytask_id = data.get("id")
        try:
            dailytask = DailyTask.objects.get(pk=dailytask_id)
        except (DailyTask.DoesNotExist, ValueError, TypeError):
            return ErrorMessage(
                "Daily task with id '{}' does not exist!".format(dailytask_id)
            ).as_json

        form = DailyTaskAPIForm(data, instance=dailytask)

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
    ARGUMENTS = (["id", "task", "arguments", "priority"],)

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


class EditEnclosureCommand(BaseAPIView):

    METHOD = "POST"
    URL = "/enclosure/edit"
    URL_POST = "/enclosure/edit"
    ARGUMENTS = (["id", "name", "platform", "netbox_id", "description", "is_virtual"],)

    HELP_SHORT = "Edits an enclosure in the database."
    HELP = """Edits an enclosure in the database (superusers only).

    Usage:
        EDIT enclosure <id>
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^enclosure/edit",
                EditEnclosureCommand.as_view(),
                name="enclosure_edit",
            ),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return form for editing an enclosure."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        enclosure_id = request.GET.get("id")
        try:
            enclosure = Enclosure.objects.get(pk=enclosure_id)  # type: ignore[misc]
        except (Enclosure.DoesNotExist, ValueError, TypeError):
            return ErrorMessage(
                "Enclosure with id '{}' does not exist!".format(enclosure_id)
            ).as_json

        form = EnclosureAPIForm(instance=enclosure)
        fields = form.as_dict()
        fields["id"] = {
            "type": "INTEGER",
            "prompt": "ID",
            "initial": enclosure.pk,
            "required": True,
        }

        input = InputSerializer(fields, self.URL_POST, ["id"] + form.get_order())
        return input.as_json

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Edit enclosure."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        enclosure_id = data.get("id")
        try:
            enclosure = Enclosure.objects.get(pk=enclosure_id)
        except (Enclosure.DoesNotExist, ValueError, TypeError):
            return ErrorMessage(
                "Enclosure with id '{}' does not exist!".format(enclosure_id)
            ).as_json

        form = EnclosureAPIForm(data, instance=enclosure)

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


class EditRemotePowerDeviceCommand(BaseAPIView):

    METHOD = "POST"
    URL = "/remotepowerdevice/edit"
    URL_POST = "/remotepowerdevice/edit"
    ARGUMENTS = (["id", "fqdn", "mac", "username", "password", "fence_agent", "url"],)

    HELP_SHORT = "Edits a remote power device in the database."
    HELP = """Edits a remote power device in the database (superusers only).

    Usage:
        EDIT remotepowerdevice <id>
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^remotepowerdevice/edit",
                EditRemotePowerDeviceCommand.as_view(),
                name="remotepowerdevice_edit",
            ),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return form for editing a remote power device."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        remotepowerdevice_id = request.GET.get("id")
        try:
            remotepowerdevice = RemotePowerDevice.objects.get(pk=remotepowerdevice_id)  # type: ignore[misc]
        except (RemotePowerDevice.DoesNotExist, ValueError, TypeError):
            return ErrorMessage(
                "Remote power device with id '{}' does not exist!".format(
                    remotepowerdevice_id
                )
            ).as_json

        form = RemotePowerDeviceAPIForm(instance=remotepowerdevice)
        fields = form.as_dict()
        fields["id"] = {
            "type": "INTEGER",
            "prompt": "ID",
            "initial": remotepowerdevice.pk,
            "required": True,
        }

        input = InputSerializer(fields, self.URL_POST, ["id"] + form.get_order())
        return input.as_json

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Edit remote power device."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        remotepowerdevice_id = data.get("id")
        try:
            remotepowerdevice = RemotePowerDevice.objects.get(pk=remotepowerdevice_id)
        except (RemotePowerDevice.DoesNotExist, ValueError, TypeError):
            return ErrorMessage(
                "Remote power device with id '{}' does not exist!".format(
                    remotepowerdevice_id
                )
            ).as_json

        form = RemotePowerDeviceAPIForm(data, instance=remotepowerdevice)

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


class EditDomainArchitectureCommand(BaseAPIView):

    METHOD = "POST"
    URL = "/domainarchitecture/edit"
    URL_POST = "/domainarchitecture/edit"
    ARGUMENTS = (["id", "domain", "arch", "contact_email"],)

    HELP_SHORT = "Edits a supported architecture entry for a domain."
    HELP = """Edits a supported architecture entry for a domain (superusers only).

    Usage:
        EDIT domainarchitecture <id>
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^domainarchitecture/edit",
                EditDomainArchitectureCommand.as_view(),
                name="domainarchitecture_edit",
            ),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return form for editing a supported architecture entry for a domain."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        domainarchitecture_id = request.GET.get("id")
        try:
            domainarchitecture = DomainAdmin.objects.get(pk=domainarchitecture_id)  # type: ignore[misc]
        except (DomainAdmin.DoesNotExist, ValueError, TypeError):
            return ErrorMessage(
                "Domain architecture entry with id '{}' does not exist!".format(
                    domainarchitecture_id
                )
            ).as_json

        form = DomainArchitectureAPIForm(instance=domainarchitecture)
        fields = form.as_dict()
        fields["id"] = {
            "type": "INTEGER",
            "prompt": "ID",
            "initial": domainarchitecture.pk,
            "required": True,
        }

        input = InputSerializer(fields, self.URL_POST, ["id"] + form.get_order())
        return input.as_json

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Edit supported architecture entry for a domain."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        domainarchitecture_id = data.get("id")
        try:
            domainarchitecture = DomainAdmin.objects.get(pk=domainarchitecture_id)
        except (DomainAdmin.DoesNotExist, ValueError, TypeError):
            return ErrorMessage(
                "Domain architecture entry with id '{}' does not exist!".format(
                    domainarchitecture_id
                )
            ).as_json

        form = DomainArchitectureAPIForm(data, instance=domainarchitecture)

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


class EditDomainCommand(BaseAPIView):

    METHOD = "POST"
    URL = "/domain/edit"
    URL_POST = "/domain/edit"
    ARGUMENTS = (
        [
            "id",
            "name",
            "cobbler_server",
            "cobbler_server_username",
            "cobbler_server_password",
            "tftp_server",
            "cscreen_server",
            "ip_v4",
            "ip_v6",
            "subnet_mask_v4",
            "subnet_mask_v6",
            "enable_v4",
            "enable_v6",
            "dynamic_range_v4_start",
            "dynamic_range_v4_end",
            "dynamic_range_v6_start",
            "dynamic_range_v6_end",
        ],
    )

    HELP_SHORT = "Edits a domain in the database."
    HELP = """Edits a domain in the database (superusers only).

    Usage:
        EDIT domain <id>
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^domain/edit",
                EditDomainCommand.as_view(),
                name="domain_edit",
            ),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return form for editing a domain."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        domain_id = request.GET.get("id")
        try:
            domain = Domain.objects.get(pk=domain_id)  # type: ignore[misc]
        except (Domain.DoesNotExist, ValueError, TypeError):
            return ErrorMessage(
                "Domain with id '{}' does not exist!".format(domain_id)
            ).as_json

        form = DomainAPIForm(instance=domain)
        fields = form.as_dict()
        fields["id"] = {
            "type": "INTEGER",
            "prompt": "ID",
            "initial": domain.pk,
            "required": True,
        }

        input = InputSerializer(fields, self.URL_POST, ["id"] + form.get_order())
        return input.as_json

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Edit domain."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        domain_id = data.get("id")
        try:
            domain = Domain.objects.get(pk=domain_id)
        except (Domain.DoesNotExist, ValueError, TypeError):
            return ErrorMessage(
                "Domain with id '{}' does not exist!".format(domain_id)
            ).as_json

        form = DomainAPIForm(data, instance=domain)

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


class EditNetworkInterfaceCommand(BaseAPIView):

    METHOD = "POST"
    URL = "/networkinterface/edit"
    URL_POST = "/networkinterface/edit"
    ARGUMENTS = (["id", "primary", "mac_address", "ip_address_v4", "ip_address_v6"],)

    HELP_SHORT = "Edits a network interface in the database."
    HELP = """Edits a network interface in the database (superusers only).

    Usage:
        EDIT networkinterface <id>
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^networkinterface/edit",
                EditNetworkInterfaceCommand.as_view(),
                name="networkinterface_edit",
            ),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return form for editing a network interface."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        networkinterface_id = request.GET.get("id")
        try:
            networkinterface = NetworkInterface.objects.get(pk=networkinterface_id)  # type: ignore[misc]
        except (NetworkInterface.DoesNotExist, ValueError, TypeError):
            return ErrorMessage(
                "Network interface with id '{}' does not exist!".format(
                    networkinterface_id
                )
            ).as_json

        form = NetworkInterfaceAPIForm(instance=networkinterface)
        fields = form.as_dict()
        fields["id"] = {
            "type": "INTEGER",
            "prompt": "ID",
            "initial": networkinterface.pk,
            "required": True,
        }

        input = InputSerializer(fields, self.URL_POST, ["id"] + form.get_order())
        return input.as_json

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Edit network interface."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        networkinterface_id = data.get("id")
        try:
            networkinterface = NetworkInterface.objects.get(pk=networkinterface_id)
        except (NetworkInterface.DoesNotExist, ValueError, TypeError):
            return ErrorMessage(
                "Network interface with id '{}' does not exist!".format(
                    networkinterface_id
                )
            ).as_json

        form = NetworkInterfaceAPIForm(data, instance=networkinterface)

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


class EditSerialConsoleCommandGet(BaseAPIView):

    URL_POST = "/serialconsole/{fqdn}/edit"

    HELP_SHORT = "Edits the serial console of a machine."
    HELP = """Edits the serial console of a machine (superusers only).

    Usage:
        EDIT serialconsole <fqdn>
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^serialconsole/edit",
                EditSerialConsoleCommandGet.as_view(),
                name="serialconsole_edit_get",
            ),
        ]

    def get(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> Union[JsonResponse, HttpResponseRedirect]:
        """Return form for editing a serial console."""
        fqdn = request.GET.get("fqdn", "")
        try:
            result = get_machine(
                fqdn, redirect_to="api:serialconsole_edit_get", data=request.GET
            )
            if isinstance(result, Serializer):
                return result.as_json
            elif isinstance(result, HttpResponseRedirect):
                return result
            machine = result
        except Exception as e:
            return ErrorMessage(str(e)).as_json

        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        if not machine.has_serialconsole():
            return ErrorMessage("Machine has no serial console!").as_json

        serialconsole = machine.serialconsole
        form = SerialConsoleAPIForm(machine=machine)
        for field_name in form._query_fields:  # type: ignore
            form.fields[field_name].initial = getattr(serialconsole, field_name)

        input = InputSerializer(
            form.as_dict(), self.URL_POST.format(fqdn=machine.fqdn), form.get_order()
        )
        return input.as_json


class EditSerialConsoleCommandPost(BaseAPIView):

    URL_POST = "/serialconsole/{fqdn}/edit"

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^serialconsole/(?P<fqdn>[a-z0-9\.-]+)/edit$",
                EditSerialConsoleCommandPost.as_view(),
                name="serialconsole_edit_post",
            ),
        ]

    def post(
        self, request: Request, fqdn: str, *args: Any, **kwargs: Any
    ) -> Union[JsonResponse, HttpResponseRedirect]:
        """Edit serial console of machine."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        try:
            result = get_machine(
                fqdn, redirect_to="api:serialconsole_edit_post", data=request.GET
            )
            if isinstance(result, Serializer):
                return result.as_json
            elif isinstance(result, HttpResponseRedirect):
                return result
            machine = result
        except Exception as e:
            return ErrorMessage(str(e)).as_json

        if not machine.has_serialconsole():
            return ErrorMessage("Machine has no serial console!").as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        form = SerialConsoleAPIForm(data, machine=machine)

        if form.is_valid():
            try:
                serialconsole = machine.serialconsole
                for field_name, value in form.cleaned_data.items():
                    if field_name == "machine":
                        continue
                    setattr(serialconsole, field_name, value)
                serialconsole.save()
            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

            return Message("Ok.").as_json

        return ErrorMessage("\n{}".format(format_cli_form_errors(form))).as_json  # type: ignore


class EditRemotePowerCommandGet(BaseAPIView):

    URL_POST = "/remotepower/{fqdn}/edit"

    HELP_SHORT = "Edits the remote power of a machine."
    HELP = """Edits the remote power of a machine (superusers only).

    Usage:
        EDIT remotepower <fqdn>
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^remotepower/edit",
                EditRemotePowerCommandGet.as_view(),
                name="remotepower_edit_get",
            ),
        ]

    def get(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> Union[JsonResponse, HttpResponseRedirect]:
        """Return form for editing a remote power."""
        fqdn = request.GET.get("fqdn", "")
        try:
            result = get_machine(
                fqdn, redirect_to="api:remotepower_edit_get", data=request.GET
            )
            if isinstance(result, Serializer):
                return result.as_json
            elif isinstance(result, HttpResponseRedirect):
                return result
            machine = result
        except Exception as e:
            return ErrorMessage(str(e)).as_json

        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        if not machine.has_remotepower():
            return ErrorMessage("Machine has no remote power!").as_json

        remotepower = machine.remotepower
        form = RemotePowerAPIForm(machine=machine)
        for field_name in form._query_fields:  # type: ignore
            form.fields[field_name].initial = getattr(remotepower, field_name)

        input = InputSerializer(
            form.as_dict(), self.URL_POST.format(fqdn=machine.fqdn), form.get_order()
        )
        return input.as_json


class EditRemotePowerCommandPost(BaseAPIView):

    URL_POST = "/remotepower/{fqdn}/edit"

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^remotepower/(?P<fqdn>[a-z0-9\.-]+)/edit$",
                EditRemotePowerCommandPost.as_view(),
                name="remotepower_edit_post",
            ),
        ]

    def post(
        self, request: Request, fqdn: str, *args: Any, **kwargs: Any
    ) -> Union[JsonResponse, HttpResponseRedirect]:
        """Edit remote power of machine."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        try:
            result = get_machine(
                fqdn, redirect_to="api:remotepower_edit_post", data=request.GET
            )
            if isinstance(result, Serializer):
                return result.as_json
            elif isinstance(result, HttpResponseRedirect):
                return result
            machine = result
        except Exception as e:
            return ErrorMessage(str(e)).as_json

        if not machine.has_remotepower():
            return ErrorMessage("Machine has no remote power!").as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        form = RemotePowerAPIForm(data, machine=machine)

        if form.is_valid():
            try:
                remotepower = machine.remotepower
                for field_name, value in form.cleaned_data.items():
                    if field_name == "machine":
                        continue
                    setattr(remotepower, field_name, value)
                remotepower.save()
            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

            return Message("Ok.").as_json

        return ErrorMessage("\n{}".format(format_cli_form_errors(form))).as_json  # type: ignore


class EditBMCCommand(BaseAPIView):

    METHOD = "POST"
    URL = "/bmc/edit"
    URL_POST = "/bmc/edit"
    ARGUMENTS = (
        [
            "id",
            "fqdn",
            "mac",
            "username",
            "password",
            "fence_agent",
            "ip_address_v4",
            "ip_address_v6",
        ],
    )

    HELP_SHORT = "Edits a BMC in the database."
    HELP = """Edits a BMC in the database (superusers only).

    Usage:
        EDIT bmc <id>
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^bmc/edit",
                EditBMCCommand.as_view(),
                name="bmc_edit",
            ),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return form for editing a BMC."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        bmc_id = request.GET.get("id")
        try:
            bmc = BMC.objects.get(pk=bmc_id)  # type: ignore[misc]
        except (BMC.DoesNotExist, ValueError, TypeError):
            return ErrorMessage(
                "BMC with id '{}' does not exist!".format(bmc_id)
            ).as_json

        form = BMCAPIForm(machine=bmc.machine)
        for field_name in form._query_fields:  # type: ignore
            form.fields[field_name].initial = getattr(bmc, field_name)
        fields = form.as_dict()
        fields["id"] = {
            "type": "INTEGER",
            "prompt": "ID",
            "initial": bmc.pk,
            "required": True,
        }

        input = InputSerializer(fields, self.URL_POST, ["id"] + list(form.get_order()))
        return input.as_json

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Edit BMC."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        bmc_id = data.get("id")
        try:
            bmc = BMC.objects.get(pk=bmc_id)
        except (BMC.DoesNotExist, ValueError, TypeError):
            return ErrorMessage(
                "BMC with id '{}' does not exist!".format(bmc_id)
            ).as_json

        form = BMCAPIForm(data, machine=bmc.machine)

        if form.is_valid():
            try:
                for field_name, value in form.cleaned_data.items():
                    setattr(bmc, field_name, value)
                bmc.save()
            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

            return Message("Ok.").as_json

        return ErrorMessage(
            "\n{}".format(format_cli_form_errors(form))  # type: ignore[arg-type]
        ).as_json
