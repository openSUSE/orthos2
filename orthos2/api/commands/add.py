import json
import logging
from typing import Any, List, Union

from django.contrib.auth.models import AnonymousUser
from django.http import (
    HttpResponsePermanentRedirect,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import redirect
from django.urls import URLPattern, re_path, reverse
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from orthos2.api.commands.base import BaseAPIView, get_machine
from orthos2.api.forms import (
    AnnotationAPIForm,
    BMCAPIForm,
    MachineAPIForm,
    RemotePowerAPIForm,
    RemotePowerDeviceAPIForm,
    SerialConsoleAPIForm,
    VirtualMachineAPIForm,
)
from orthos2.api.serializers.misc import (
    AuthRequiredSerializer,
    ErrorMessage,
    InfoMessage,
    InputSerializer,
    Message,
    Serializer,
)
from orthos2.data.models import (
    BMC,
    Annotation,
    Machine,
    RemotePower,
    RemotePowerDevice,
    SerialConsole,
)
from orthos2.utils.misc import add_offset_to_date, format_cli_form_errors

logger = logging.getLogger("api")


class Add:
    MACHINE = "machine"
    VIRTUALMACHINE = "virtualmachine"
    SERIALCONSOLE = "serialconsole"
    ANNOTATION = "annotation"
    REMOTEPOWER = "remotepower"
    BMC = "bmc"
    REMOTEPOWERDEVICE = "remotepowerdevice"

    as_list = [
        MACHINE,
        VIRTUALMACHINE,
        SERIALCONSOLE,
        ANNOTATION,
        REMOTEPOWER,
        BMC,
        REMOTEPOWERDEVICE,
    ]


class AddCommand(BaseAPIView):

    METHOD = "GET"
    URL = "/add"
    ARGUMENTS = (["args*"],)

    HELP_SHORT = "Adds information to the database."
    HELP = """Adds items to the database. All information will be queried interactively.

    Usage:
        ADD <item> [args*]

    Arguments:
        item - Specify the item which should be added. Items are:

                machine                       : Add a machine (superusers only).
                annotation <fqdn>             : Add an annotation to a specific
                                                machine (no bugreports).
                serialconsole <fqdn>          : Add a serial console to a specific
                                                machine (superusers only).
                remotepower <fqdn>            : Add a remote power to a specific
                                                machine (superusers only).
                virtualmachine <architecture> : Add a virtual machine on a specific
                                                architecture.
                bmc <fqdn>                    : Add a bmc to a machine.

    Example:
        ADD machine
        ADD virtualmachine x86_64
        ADD serialconsole foo.domain.tld
        ADD remotepower foo.domain.tld
        ADD annotation foo.domain.tld
        ADD bmc foo.domain.tld
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(r"^add$", AddCommand.as_view(), name="add"),
        ]

    @staticmethod
    def get_tabcompletion() -> List[str]:
        return Add.as_list

    def get(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> Union[JsonResponse, HttpResponsePermanentRedirect, HttpResponseRedirect]:
        """Dispatcher for the 'add' command."""
        arguments = request.GET.get("args", None)

        if arguments:
            arguments = arguments.split()  # type: ignore
            item = arguments[0].lower()
            sub_arguments = arguments[1:]
        else:
            return ErrorMessage("Item is missing!").as_json

        if item == Add.VIRTUALMACHINE:
            if len(sub_arguments) != 1:
                return ErrorMessage(
                    "Invalid number of arguments for 'virtualmachine'!"
                ).as_json

            return redirect(
                "{}?arch={}".format(reverse("api:vm_add"), sub_arguments[0])
            )

        elif item == Add.MACHINE:
            if sub_arguments:
                return ErrorMessage(
                    "Invalid number of arguments for 'machine'!"
                ).as_json

            return redirect(reverse("api:machine_add"))

        elif item == Add.SERIALCONSOLE:
            if len(sub_arguments) != 1:
                return ErrorMessage(
                    "Invalid number of arguments for 'serialconsole'!"
                ).as_json

            return redirect(
                "{}?fqdn={}".format(reverse("api:serialconsole_add"), sub_arguments[0])
            )

        elif item == Add.ANNOTATION:
            if len(sub_arguments) != 1:
                return ErrorMessage(
                    "Invalid number of arguments for 'annotation'!"
                ).as_json

            return redirect(
                "{}?fqdn={}".format(reverse("api:annotation_add"), sub_arguments[0])
            )

        elif item == Add.REMOTEPOWER:
            if len(sub_arguments) != 1:
                return ErrorMessage(
                    "Invalid number of arguments for 'remotepower'!"
                ).as_json

            return redirect(
                "{}?fqdn={}".format(reverse("api:remotepower_add"), sub_arguments[0])
            )
        elif item == Add.REMOTEPOWERDEVICE:
            if sub_arguments:
                return ErrorMessage(
                    "Invalid number of arguments for 'remotepowerdevice'!"
                ).as_json
            return redirect(reverse("api:remotepowerdevice_add"))

        elif item == Add.BMC:
            if len(sub_arguments) != 1:
                return ErrorMessage("Invalid number of arguments for 'bmc'!").as_json

            return redirect(
                "{}?fqdn={}".format(reverse("api:bmc_add"), sub_arguments[0])
            )

        return ErrorMessage("Unknown item '{}'!".format(item)).as_json


class AddVMCommand(BaseAPIView):

    URL_POST = "/vm/{arch}/add"

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(r"^vm/add", AddVMCommand.as_view(), name="vm_add"),
            re_path(
                r"^vm/(?P<architecture>[a-z0-9\.-_]+)/add$",
                AddVMCommand.as_view(),
                name="vm_add",
            ),
        ]

    def _get_available_architectures(self) -> List[str]:
        """Return list of available architectures for virtual machines."""
        architectures = list(
            Machine.api.filter(vm_dedicated_host=True)
            .order_by()
            .values_list("architecture__name", flat=True)
            .distinct()
        )
        return architectures

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return form for adding a virtual machine."""
        architectures = self._get_available_architectures()
        architecture = request.GET.get("arch", "")

        if architecture.lower() not in architectures:
            return Message(
                "Available architectures: {}".format("|".join(architectures))
            ).as_json

        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        hosts = Machine.api.filter(
            vm_dedicated_host=True, architecture__name=architecture
        )
        host = None

        for host_ in hosts:
            if host_.virtualization_api and (
                host_.get_virtual_machines().count() < host_.vm_max  # type: ignore
            ):
                host = host_
                break

        if host is None:
            return ErrorMessage("No virtual machine hosts left!").as_json

        form = VirtualMachineAPIForm(virtualization_api=host.virtualization_api)

        input = InputSerializer(
            form.as_dict(host),
            self.URL_POST.format(arch=architecture),
            form.get_order(),
        )
        return input.as_json

    def post(
        self, request: Request, architecture: Any, *args: Any, **kwargs: Any
    ) -> JsonResponse:
        """Add virtual machine for specific `architecture`."""
        data = json.loads(request.body.decode("utf-8"))["form"]

        try:
            host = Machine.api.get(fqdn__iexact=data["host"], vm_dedicated_host=True)
        except Machine.DoesNotExist:
            return ErrorMessage("Host doesn't exist!").as_json
        except Exception as e:
            return ErrorMessage(str(e)).as_json

        if not host.virtualization_api:
            return ErrorMessage("No virtualization API available!").as_json

        form = VirtualMachineAPIForm(data, virtualization_api=host.virtualization_api)

        if form.is_valid():
            try:
                vm = host.virtualization_api.create(**form.cleaned_data)

                vm.reserve(
                    reason="VM of {}".format(request.user),
                    until=add_offset_to_date(30),  # type: ignore
                    user=request.user,  # type: ignore
                )

                theader = [
                    {"fqdn": "FQDN"},
                    {"mac_address": "MAC address"},
                ]
                if vm.vnc["enabled"]:  # type: ignore
                    theader.append({"vnc": "VNC"})

                response = {
                    "header": {"type": "TABLE", "theader": theader},
                    "data": [{"fqdn": vm.fqdn, "mac_address": vm.mac_address}],
                }
                if vm.vnc["enabled"]:  # type: ignore
                    response["data"][0]["vnc"] = "{}:{}".format(  # type: ignore
                        host.fqdn, vm.vnc["port"]  # type: ignore
                    )

                return JsonResponse(response)

            except Exception as e:
                return ErrorMessage(str(e)).as_json

        return ErrorMessage("\n{}".format(format_cli_form_errors(form))).as_json


class AddMachineCommand(BaseAPIView):

    URL_POST = "/machine/add"

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(r"^machine/add", AddMachineCommand.as_view(), name="machine_add"),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return form for adding a machine."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        form = MachineAPIForm()

        input = InputSerializer(form.as_dict(), self.URL_POST, form.get_order())
        return input.as_json

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Add machine."""
        if not request.user.is_superuser:
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        form = MachineAPIForm(data)

        if form.is_valid():

            cleaned_data = form.cleaned_data
            mac_address = cleaned_data["mac_address"]
            del cleaned_data["mac_address"]
            hypervisor = None
            if cleaned_data["hypervisor_fqdn"]:
                try:
                    hypervisor = Machine.objects.get(
                        fqdn=cleaned_data["hypervisor_fqdn"]
                    )
                except Machine.DoesNotExist:
                    return ErrorMessage(
                        "Hypervisor [%s] does not exist"
                        % cleaned_data["hypervisor_fqdn"]
                    ).as_json
            del cleaned_data["hypervisor_fqdn"]
            new_machine = Machine(**cleaned_data)
            new_machine.hypervisor = hypervisor
            new_machine.mac_address = mac_address
            try:
                new_machine.save()
            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

            return Message("Ok.").as_json

        return ErrorMessage("\n{}".format(format_cli_form_errors(form))).as_json


class AddBMCCommand(BaseAPIView):
    permission_classes = [IsAuthenticated]
    URL_POST = "/bmc/add/{fqdn}"

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(r"^bmc/add", AddBMCCommand.as_view(), name="bmc_add"),
            re_path(
                r"^bmc/add/(?P<fqdn>[a-z0-9.-]+)/$",
                AddBMCCommand.as_view(),
                name="bmc_add",
            ),
        ]

    def get(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> Union[JsonResponse, HttpResponseRedirect]:
        """Return form for adding an BMC."""
        fqdn = request.GET.get("fqdn", "")
        try:
            result = get_machine(fqdn, redirect_to="api:bmc_add", data=request.GET)
            if isinstance(result, Serializer):
                return result.as_json
            elif isinstance(result, HttpResponseRedirect):
                return result
            machine = result
        except Exception as e:
            return ErrorMessage(str(e)).as_json

        form = BMCAPIForm(machine=machine)

        input_serializer = InputSerializer(
            form.as_dict(), self.URL_POST.format(fqdn=machine.fqdn), form.get_order()
        )
        return input_serializer.as_json

    def post(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> Union[JsonResponse, HttpResponseRedirect]:
        """Add BMC to machine."""
        try:
            # FIXME: When you call /bmc/add/ the machine is add
            fqdn = request.path.split("/")[-1]
            result = get_machine(fqdn, redirect_to="api:bmc_add", data=request.GET)
            if isinstance(result, Serializer):
                return result.as_json
            elif isinstance(result, HttpResponseRedirect):
                return result
            machine = result
        except Exception as e:
            return ErrorMessage(str(e)).as_json

        data = json.loads(request.body.decode("utf-8")).get("form", "")
        form = BMCAPIForm(data, machine=machine)

        if form.is_valid():
            try:
                cleaned_data = form.cleaned_data
                bmc = BMC(
                    machine=machine,
                    fqdn=cleaned_data["fqdn"],
                    mac=cleaned_data["mac"],
                    username=cleaned_data["username"],
                    password=cleaned_data["password"],
                    fence_name=cleaned_data["fence_name"],
                )
                bmc.save()
            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

            return Message("Ok.").as_json

        return ErrorMessage("\n{}".format(format_cli_form_errors(form))).as_json


class AddSerialConsoleCommand(BaseAPIView):

    URL_POST = "/serialconsole/{fqdn}/add"

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^serialconsole/add",
                AddSerialConsoleCommand.as_view(),
                name="serialconsole_add",
            ),
            re_path(
                r"^serialconsole/(?P<fqdn>[a-z0-9\.-]+)/add$",
                AddSerialConsoleCommand.as_view(),
                name="serialconsole_add",
            ),
        ]

    def get(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> Union[JsonResponse, HttpResponseRedirect]:
        """Return form for adding a machine."""
        fqdn = request.GET.get("fqdn", "")
        try:
            result = get_machine(
                fqdn, redirect_to="api:serialconsole_add", data=request.GET
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

        if not request.user.is_superuser:
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        if machine.has_serialconsole():
            return InfoMessage("Machine has already a serial console.").as_json

        form = SerialConsoleAPIForm(machine=machine)

        input = InputSerializer(
            form.as_dict(), self.URL_POST.format(fqdn=machine.fqdn), form.get_order()
        )
        return input.as_json

    def post(
        self, request: Request, fqdn: str, *args: Any, **kwargs: Any
    ) -> Union[JsonResponse, HttpResponseRedirect]:
        """Add serial console to machine."""
        if not request.user.is_superuser:
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        try:
            result = get_machine(
                fqdn, redirect_to="api:serialconsole_add", data=request.GET
            )
            if isinstance(result, Serializer):
                return result.as_json
            elif isinstance(result, HttpResponseRedirect):
                return result
            machine = result
        except Exception as e:
            return ErrorMessage(str(e)).as_json

        if machine.has_serialconsole():
            return InfoMessage("Machine has already a serial console.").as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        form = SerialConsoleAPIForm(data, machine=machine)

        if form.is_valid():
            try:
                serialconsole = SerialConsole(**form.cleaned_data)
                serialconsole.save()
            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

            return Message("Ok.").as_json

        return ErrorMessage("\n{}".format(format_cli_form_errors(form))).as_json


class AddAnnotationCommand(BaseAPIView):

    URL_POST = "/annotation/{fqdn}/add"

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^annotation/add",
                AddAnnotationCommand.as_view(),
                name="annotation_add",
            ),
            re_path(
                r"^annotation/(?P<fqdn>[a-z0-9\.-]+)/add$",
                AddAnnotationCommand.as_view(),
                name="annotation_add",
            ),
        ]

    def get(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> Union[JsonResponse, HttpResponseRedirect]:
        """Return form for adding an annotation."""
        fqdn = request.GET.get("fqdn", "")
        try:
            result = get_machine(
                fqdn, redirect_to="api:annotation_add", data=request.GET
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

        form = AnnotationAPIForm(machine=machine)

        input = InputSerializer(
            form.as_dict(), self.URL_POST.format(fqdn=machine.fqdn), form.get_order()
        )
        return input.as_json

    def post(
        self, request: Request, fqdn: str, *args: Any, **kwargs: Any
    ) -> Union[JsonResponse, HttpResponseRedirect]:
        """Add annotation to machine."""
        try:
            result = get_machine(
                fqdn, redirect_to="api:annotation_add", data=request.GET
            )
            if isinstance(result, Serializer):
                return result.as_json
            elif isinstance(result, HttpResponseRedirect):
                return result
            machine = result
        except Exception as e:
            return ErrorMessage(str(e)).as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        form = AnnotationAPIForm(data, machine=machine)

        if form.is_valid():
            try:
                cleaned_data = form.cleaned_data
                annotation = Annotation(  # type: ignore
                    machine_id=machine.pk,
                    reporter=request.user,
                    text=cleaned_data["text"],
                )
                annotation.save()
            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

            return Message("Ok.").as_json

        return ErrorMessage("\n{}".format(format_cli_form_errors(form))).as_json


class AddRemotePowerCommand(BaseAPIView):

    URL_POST = "/remotepower/add/{fqdn}"

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^remotepower/add",
                AddRemotePowerCommand.as_view(),
                name="remotepower_add",
            ),
            re_path(
                r"^remotepower/add/(?P<fqdn>[a-z0-9\.-]+)$/",
                AddRemotePowerCommand.as_view(),
                name="remotepower_add",
            ),
        ]

    def get(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> Union[JsonResponse, HttpResponseRedirect]:
        """Return form for adding a remotepower."""
        fqdn = request.GET.get("fqdn", None)
        if fqdn is None:
            return ErrorMessage("No FQDN given").as_json
        try:
            result = get_machine(
                fqdn, redirect_to="api:remotepower_add", data=request.GET
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

        if not request.user.is_superuser:
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        if machine.has_remotepower():
            return InfoMessage("Machine has already a remote power.").as_json

        form = RemotePowerAPIForm(machine=machine)

        input = InputSerializer(
            form.as_dict(), self.URL_POST.format(fqdn=machine.fqdn), form.get_order()
        )
        return input.as_json

    def post(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> Union[JsonResponse, HttpResponseRedirect]:
        """Add remote power to machine."""
        if not request.user.is_superuser:
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        try:
            fqdn = request.path.split("/")[-1]
            result = get_machine(
                fqdn, redirect_to="api:remotepower_add", data=request.GET
            )
            if isinstance(result, Serializer):
                return result.as_json
            elif isinstance(result, HttpResponseRedirect):
                return result
            machine = result
        except Exception as e:
            return ErrorMessage(str(e)).as_json

        if machine.has_remotepower():
            return InfoMessage("Machine has already a remote power.").as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        form = RemotePowerAPIForm(data, machine=machine)

        if form.is_valid():
            try:
                remotepower = RemotePower(**form.cleaned_data)
                remotepower.save()
            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

            return Message("Ok.").as_json

        return ErrorMessage("\n{}".format(format_cli_form_errors(form))).as_json


class AddRemotePowerDeviceCommand(BaseAPIView):

    URL_POST = "/remotepowerdevice/add"

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^remotepowerdevice/add",
                AddRemotePowerDeviceCommand.as_view(),
                name="remotepowerdevice_add",
            ),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return form for adding a remotepowerdevice."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        form = RemotePowerDeviceAPIForm()

        input = InputSerializer(form.as_dict(), self.URL_POST, form.get_order())  # type: ignore
        return input.as_json

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Add remotepowerdevice."""
        if not request.user.is_superuser:
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        form = RemotePowerDeviceAPIForm(data)

        if form.is_valid():

            cleaned_data = form.cleaned_data
            new_device = RemotePowerDevice(
                username=cleaned_data["username"],
                password=cleaned_data["password"],
                mac=cleaned_data["mac"],
                fqdn=cleaned_data["fqdn"],
                fence_name=cleaned_data["fence_name"],
            )

            try:
                new_device.save()
            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

            return Message("Ok.").as_json

        return ErrorMessage("\n{}".format(format_cli_form_errors(form))).as_json  # type: ignore
