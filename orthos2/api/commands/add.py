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
    AnnotationAPIForm,
    ArchitectureAPIForm,
    BMCAPIForm,
    DailyTaskAPIForm,
    DeviceTypeAPIForm,
    DomainAPIForm,
    DomainArchitectureAPIForm,
    EnclosureAPIForm,
    MachineAPIForm,
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
from orthos2.data.models import BMC, Annotation, Machine, RemotePower, SerialConsole
from orthos2.data.models.networkinterface import NetworkInterface
from orthos2.data.models.remotepowertype import RemotePowerType
from orthos2.utils.misc import (
    add_offset_to_date,
    format_cli_form_errors,
    suggest_host_ip,
)

logger = logging.getLogger("api")


class Add:
    MACHINE = "machine"
    VIRTUALMACHINE = "virtualmachine"
    SERIALCONSOLE = "serialconsole"
    ANNOTATION = "annotation"
    REMOTEPOWER = "remotepower"
    BMC = "bmc"
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
    NETWORKINTERFACE = "networkinterface"

    as_list = [
        MACHINE,
        VIRTUALMACHINE,
        SERIALCONSOLE,
        ANNOTATION,
        REMOTEPOWER,
        BMC,
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
        NETWORKINTERFACE,
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
                manufacturer <name>           : Add a manufacturer (superusers only).
                devicetype <name>             : Add a device type (superusers only).
                serialconsoletype <name>      : Add a serial console type
                                                (superusers only).
                system <name>                 : Add a system (superusers only).
                remotepowertype <name>        : Add a remote power type
                                                (superusers only).
                architecture <name>           : Add an architecture
                                                (superusers only).
                serverconfig <key> <value>    : Add a server configuration entry
                                                (superusers only).
                enclosure <name>              : Add an enclosure (superusers only).
                domainarchitecture            : Add a supported architecture entry
                                                for a domain (superusers only).
                domain <name>                 : Add a domain (superusers only).
                networkinterface <fqdn>       : Add a network interface to a
                                                specific machine (superusers only).

    Example:
        ADD machine
        ADD virtualmachine x86_64
        ADD serialconsole foo.domain.tld
        ADD remotepower foo.domain.tld
        ADD annotation foo.domain.tld
        ADD bmc foo.domain.tld
        ADD manufacturer Dell
        ADD devicetype PowerEdge
        ADD serialconsoletype Telnet
        ADD system BareMetal
        ADD remotepowertype "Dummy BMC"
        ADD architecture x86_64
        ADD serverconfig foo.bar baz
        ADD enclosure Rack01
        ADD domainarchitecture
        ADD domain foo.domain.tld
        ADD networkinterface foo.domain.tld
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
                "{}?fqdn={}".format(
                    reverse("api:serialconsole_add_get"), sub_arguments[0]
                )
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
                "{}?fqdn={}".format(
                    reverse("api:remotepower_add_get"), sub_arguments[0]
                )
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
                "{}?fqdn={}".format(reverse("api:bmc_add_get"), sub_arguments[0])
            )

        elif item == Add.MANUFACTURER:
            if sub_arguments:
                return ErrorMessage(
                    "Invalid number of arguments for 'manufacturer'!"
                ).as_json
            return redirect(reverse("api:manufacturer_add"))

        elif item == Add.DEVICETYPE:
            if sub_arguments:
                return ErrorMessage(
                    "Invalid number of arguments for 'devicetype'!"
                ).as_json
            return redirect(reverse("api:devicetype_add"))

        elif item == Add.SERIALCONSOLETYPE:
            if sub_arguments:
                return ErrorMessage(
                    "Invalid number of arguments for 'serialconsoletype'!"
                ).as_json
            return redirect(reverse("api:serialconsoletype_add"))

        elif item == Add.SYSTEM:
            if sub_arguments:
                return ErrorMessage("Invalid number of arguments for 'system'!").as_json
            return redirect(reverse("api:system_add"))

        elif item == Add.REMOTEPOWERTYPE:
            if sub_arguments:
                return ErrorMessage(
                    "Invalid number of arguments for 'remotepowertype'!"
                ).as_json
            return redirect(reverse("api:remotepowertype_add"))

        elif item == Add.ARCHITECTURE:
            if sub_arguments:
                return ErrorMessage(
                    "Invalid number of arguments for 'architecture'!"
                ).as_json
            return redirect(reverse("api:architecture_add"))

        elif item == Add.SERVERCONFIG:
            if sub_arguments:
                return ErrorMessage(
                    "Invalid number of arguments for 'serverconfig'!"
                ).as_json
            return redirect(reverse("api:serverconfig_add"))

        elif item == Add.ENCLOSURE:
            if sub_arguments:
                return ErrorMessage(
                    "Invalid number of arguments for 'enclosure'!"
                ).as_json
            return redirect(reverse("api:enclosure_add"))

        elif item == Add.DOMAINARCHITECTURE:
            if sub_arguments:
                return ErrorMessage(
                    "Invalid number of arguments for 'domainarchitecture'!"
                ).as_json
            return redirect(reverse("api:domainarchitecture_add"))

        elif item == Add.DOMAIN:
            if sub_arguments:
                return ErrorMessage("Invalid number of arguments for 'domain'!").as_json
            return redirect(reverse("api:domain_add"))

        elif item == Add.NETWORKINTERFACE:
            if len(sub_arguments) != 1:
                return ErrorMessage(
                    "Invalid number of arguments for 'networkinterface'!"
                ).as_json
            return redirect(
                "{}?fqdn={}".format(
                    reverse("api:networkinterface_add_get"), sub_arguments[0]
                )
            )

        return ErrorMessage("Unknown item '{}'!".format(item)).as_json


class AddVMCommandGet(BaseAPIView):

    URL_POST = "/vm/{arch}/add"

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(r"^vm/add", AddVMCommandGet.as_view(), name="vm_add_get"),
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


class AddVMCommandPost(BaseAPIView):

    URL_POST = "/vm/{arch}/add"

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^vm/(?P<architecture>[a-z0-9\.-_]+)/add$",
                AddVMCommandPost.as_view(),
                name="vm_add_post",
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

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        form = MachineAPIForm()

        input = InputSerializer(form.as_dict(), self.URL_POST, form.get_order())
        return input.as_json

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Add machine."""
        if not request.user.is_superuser:  # type: ignore
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
            try:
                new_machine.save()
            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json
            # Machine.save() resolves fqdn_domain from the fqdn, and
            # new_primary_interface.machine requires new_machine to already have a
            # primary key - both only become available after new_machine.save().
            new_primary_interface = NetworkInterface(machine=new_machine, primary=True)
            new_primary_interface.mac_address = mac_address
            if new_machine.fqdn_domain.enable_v4:
                new_primary_interface.ip_address_v4 = suggest_host_ip(
                    4, new_machine.fqdn_domain
                )
            if new_machine.fqdn_domain.enable_v6:
                new_primary_interface.ip_address_v6 = suggest_host_ip(
                    6, new_machine.fqdn_domain
                )
            new_primary_interface.save()

            return Message("Ok.").as_json

        return ErrorMessage("\n{}".format(format_cli_form_errors(form))).as_json


class AddBMCCommandGet(BaseAPIView):
    URL_POST = "/bmc/add/{fqdn}"

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(r"^bmc/add", AddBMCCommandGet.as_view(), name="bmc_add_get"),
        ]

    def get(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> Union[JsonResponse, HttpResponseRedirect]:
        """Return form for adding an BMC."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json
        fqdn = request.GET.get("fqdn", "")
        try:
            result = get_machine(fqdn, redirect_to="api:bmc_add_post", data=request.GET)
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


class AddBMCCommandPost(BaseAPIView):
    URL_POST = "/bmc/add/{fqdn}"

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^bmc/add/(?P<fqdn>[a-z0-9.-]+)/$",
                AddBMCCommandPost.as_view(),
                name="bmc_add_post",
            ),
        ]

    def post(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> Union[JsonResponse, HttpResponseRedirect]:
        """Add BMC to machine."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json
        try:
            # FIXME: When you call /bmc/add/ the machine is add
            fqdn = request.path.split("/")[-2]
            result = get_machine(fqdn, redirect_to="api:bmc_add_post", data=request.GET)
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
                try:
                    fence_agent = RemotePowerType.objects.get(
                        name=cleaned_data["fence_agent"]
                    )
                except RemotePowerType.DoesNotExist:
                    return ErrorMessage(
                        "Remote power type '{}' does not exist!".format(
                            cleaned_data["fence_agent"]
                        )
                    ).as_json
                bmc = BMC(
                    machine=machine,
                    fqdn=cleaned_data["fqdn"],
                    mac=cleaned_data["mac"],
                    username=cleaned_data["username"],
                    password=cleaned_data["password"],
                    fence_agent=fence_agent,
                )
                bmc.save()
            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

            return Message("Ok.").as_json

        return ErrorMessage("\n{}".format(format_cli_form_errors(form))).as_json


class AddSerialConsoleCommandGet(BaseAPIView):

    URL_POST = "/serialconsole/{fqdn}/add"

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^serialconsole/add",
                AddSerialConsoleCommandGet.as_view(),
                name="serialconsole_add_get",
            ),
        ]

    def get(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> Union[JsonResponse, HttpResponseRedirect]:
        """Return form for adding a machine."""
        fqdn = request.GET.get("fqdn", "")
        try:
            result = get_machine(
                fqdn, redirect_to="api:serialconsole_add_get", data=request.GET
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

        if machine.has_serialconsole():
            return InfoMessage("Machine has already a serial console.").as_json

        form = SerialConsoleAPIForm(machine=machine)

        input = InputSerializer(
            form.as_dict(), self.URL_POST.format(fqdn=machine.fqdn), form.get_order()
        )
        return input.as_json


class AddSerialConsoleCommandPost(BaseAPIView):

    URL_POST = "/serialconsole/{fqdn}/add"

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^serialconsole/(?P<fqdn>[a-z0-9\.-]+)/add$",
                AddSerialConsoleCommandPost.as_view(),
                name="serialconsole_add_post",
            ),
        ]

    def post(
        self, request: Request, fqdn: str, *args: Any, **kwargs: Any
    ) -> Union[JsonResponse, HttpResponseRedirect]:
        """Add serial console to machine."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        try:
            result = get_machine(
                fqdn, redirect_to="api:serialconsole_add_get", data=request.GET
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


class AddAnnotationCommandGet(BaseAPIView):

    URL_POST = "/annotation/{fqdn}/add"

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^annotation/add",
                AddAnnotationCommandGet.as_view(),
                name="annotation_add_get",
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


class AddAnnotationCommandPost(BaseAPIView):

    URL_POST = "/annotation/{fqdn}/add"

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^annotation/(?P<fqdn>[a-z0-9\.-]+)/add$",
                AddAnnotationCommandPost.as_view(),
                name="annotation_add_post",
            ),
        ]

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


class AddRemotePowerCommandGet(BaseAPIView):

    URL_POST = "/remotepower/add/{fqdn}"

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^remotepower/add",
                AddRemotePowerCommandGet.as_view(),
                name="remotepower_add_get",
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
                fqdn, redirect_to="api:remotepower_add_get", data=request.GET
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

        if machine.has_remotepower():
            return InfoMessage("Machine has already a remote power.").as_json

        form = RemotePowerAPIForm(machine=machine)

        input = InputSerializer(
            form.as_dict(), self.URL_POST.format(fqdn=machine.fqdn), form.get_order()
        )
        return input.as_json


class AddRemotePowerCommandPost(BaseAPIView):

    URL_POST = "/remotepower/add/{fqdn}"

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^remotepower/add/(?P<fqdn>[a-z0-9\.-]+)/$",
                AddRemotePowerCommandPost.as_view(),
                name="remotepower_add_post",
            ),
        ]

    def post(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> Union[JsonResponse, HttpResponseRedirect]:
        """Add remote power to machine."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        try:
            fqdn = request.path.split("/")[-2]
            result = get_machine(
                fqdn, redirect_to="api:remotepower_add_get", data=request.GET
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

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        form = RemotePowerDeviceAPIForm()

        input = InputSerializer(form.as_dict(), self.URL_POST, form.get_order())  # type: ignore
        return input.as_json

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Add remotepowerdevice."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        form = RemotePowerDeviceAPIForm(data)

        if form.is_valid():
            try:
                form.save()
            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

            return Message("Ok.").as_json

        return ErrorMessage("\n{}".format(format_cli_form_errors(form))).as_json  # type: ignore


class AddManufacturerCommand(BaseAPIView):

    METHOD = "POST"
    URL = "/manufacturer/add"
    URL_POST = "/manufacturer/add"
    ARGUMENTS = (["name"],)

    HELP_SHORT = "Adds a manufacturer to the database."
    HELP = """Adds a manufacturer to the database (superusers only).

    Usage:
        ADD manufacturer <name>
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^manufacturer/add",
                AddManufacturerCommand.as_view(),
                name="manufacturer_add",
            ),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return form for adding a manufacturer."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        form = ManufacturerAPIForm()

        input = InputSerializer(form.as_dict(), self.URL_POST, form.get_order())
        return input.as_json

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Add manufacturer."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        form = ManufacturerAPIForm(data)

        if form.is_valid():
            try:
                form.save()
            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

            return Message("Ok.").as_json

        return ErrorMessage("\n{}".format(format_cli_form_errors(form))).as_json  # type: ignore


class AddDeviceTypeCommand(BaseAPIView):

    METHOD = "POST"
    URL = "/devicetype/add"
    URL_POST = "/devicetype/add"
    ARGUMENTS = (["name", "manufacturer", "is_cartridge", "description"],)

    HELP_SHORT = "Adds a device type to the database."
    HELP = """Adds a device type to the database (superusers only).

    Usage:
        ADD devicetype <name>
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^devicetype/add",
                AddDeviceTypeCommand.as_view(),
                name="devicetype_add",
            ),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return form for adding a device type."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        form = DeviceTypeAPIForm()

        input = InputSerializer(form.as_dict(), self.URL_POST, form.get_order())
        return input.as_json

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Add device type."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        form = DeviceTypeAPIForm(data)

        if form.is_valid():
            try:
                form.save()
            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

            return Message("Ok.").as_json

        return ErrorMessage("\n{}".format(format_cli_form_errors(form))).as_json  # type: ignore


class AddSerialConsoleTypeCommand(BaseAPIView):

    METHOD = "POST"
    URL = "/serialconsoletype/add"
    URL_POST = "/serialconsoletype/add"
    ARGUMENTS = (["name", "command", "comment", "has_ipmi_sol"],)

    HELP_SHORT = "Adds a serial console type to the database."
    HELP = """Adds a serial console type to the database (superusers only).

    Usage:
        ADD serialconsoletype <name>
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^serialconsoletype/add",
                AddSerialConsoleTypeCommand.as_view(),
                name="serialconsoletype_add",
            ),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return form for adding a serial console type."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        form = SerialConsoleTypeAPIForm()

        input = InputSerializer(form.as_dict(), self.URL_POST, form.get_order())
        return input.as_json

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Add serial console type."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        form = SerialConsoleTypeAPIForm(data)

        if form.is_valid():
            try:
                form.save()
            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

            return Message("Ok.").as_json

        return ErrorMessage("\n{}".format(format_cli_form_errors(form))).as_json  # type: ignore


class AddSystemCommand(BaseAPIView):

    METHOD = "POST"
    URL = "/system/add"
    URL_POST = "/system/add"
    ARGUMENTS = (["name", "virtual", "allowBMC", "allowHypervisor", "administrative"],)

    HELP_SHORT = "Adds a system to the database."
    HELP = """Adds a system to the database (superusers only).

    Usage:
        ADD system <name>
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^system/add",
                AddSystemCommand.as_view(),
                name="system_add",
            ),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return form for adding a system."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        form = SystemAPIForm()

        input = InputSerializer(form.as_dict(), self.URL_POST, form.get_order())
        return input.as_json

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Add system."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        form = SystemAPIForm(data)

        if form.is_valid():
            try:
                form.save()
            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

            return Message("Ok.").as_json

        return ErrorMessage("\n{}".format(format_cli_form_errors(form))).as_json  # type: ignore


class AddRemotePowerTypeCommand(BaseAPIView):

    METHOD = "POST"
    URL = "/remotepowertype/add"
    URL_POST = "/remotepowertype/add"
    ARGUMENTS = (
        [
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

    HELP_SHORT = "Adds a remote power type to the database."
    HELP = """Adds a remote power type to the database (superusers only).

    Usage:
        ADD remotepowertype <name>
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^remotepowertype/add",
                AddRemotePowerTypeCommand.as_view(),
                name="remotepowertype_add",
            ),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return form for adding a remote power type."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        form = RemotePowerTypeAPIForm()

        input = InputSerializer(form.as_dict(), self.URL_POST, form.get_order())
        return input.as_json

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Add remote power type."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        form = RemotePowerTypeAPIForm(data)

        if form.is_valid():
            try:
                form.save()
            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

            return Message("Ok.").as_json

        return ErrorMessage("\n{}".format(format_cli_form_errors(form))).as_json  # type: ignore


class AddArchitectureCommand(BaseAPIView):

    METHOD = "POST"
    URL = "/architecture/add"
    URL_POST = "/architecture/add"
    ARGUMENTS = (["name", "dhcp_filename", "contact_email", "default_profile"],)

    HELP_SHORT = "Adds an architecture to the database."
    HELP = """Adds an architecture to the database (superusers only).

    Usage:
        ADD architecture <name>
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^architecture/add",
                AddArchitectureCommand.as_view(),
                name="architecture_add",
            ),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return form for adding an architecture."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        form = ArchitectureAPIForm()

        input = InputSerializer(form.as_dict(), self.URL_POST, form.get_order())
        return input.as_json

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Add architecture."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        form = ArchitectureAPIForm(data)

        if form.is_valid():
            try:
                form.save()
            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

            return Message("Ok.").as_json

        return ErrorMessage("\n{}".format(format_cli_form_errors(form))).as_json  # type: ignore


class AddServerConfigCommand(BaseAPIView):

    METHOD = "POST"
    URL = "/serverconfig/add"
    URL_POST = "/serverconfig/add"
    ARGUMENTS = (["key", "value"],)

    HELP_SHORT = "Adds a server configuration entry to the database."
    HELP = """Adds a server configuration entry to the database (superusers only).

    Usage:
        ADD serverconfig <key> <value>
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^serverconfig/add",
                AddServerConfigCommand.as_view(),
                name="serverconfig_add",
            ),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return form for adding a server configuration entry."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        form = ServerConfigAPIForm()

        input = InputSerializer(form.as_dict(), self.URL_POST, form.get_order())
        return input.as_json

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Add server configuration entry."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        form = ServerConfigAPIForm(data)

        if form.is_valid():
            try:
                form.save()
            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

            return Message("Ok.").as_json

        return ErrorMessage("\n{}".format(format_cli_form_errors(form))).as_json  # type: ignore


class AddDailyTaskCommand(BaseAPIView):

    METHOD = "POST"
    URL = "/dailytask/add"
    URL_POST = "/dailytask/add"
    ARGUMENTS = (["task", "arguments", "priority", "enabled"],)

    HELP_SHORT = "Adds a daily task to the database."
    HELP = """Adds a daily task to the database (superusers only).

    Usage:
        ADD dailytask <name>
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^dailytask/add",
                AddDailyTaskCommand.as_view(),
                name="dailytask_add",
            ),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return form for adding a daily task."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        form = DailyTaskAPIForm()

        input = InputSerializer(form.as_dict(), self.URL_POST, form.get_order())
        return input.as_json

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Add daily task."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        form = DailyTaskAPIForm(data)

        if form.is_valid():
            try:
                form.save()
            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

            return Message("Ok.").as_json

        return ErrorMessage("\n{}".format(format_cli_form_errors(form))).as_json  # type: ignore


class AddSingleTaskCommand(BaseAPIView):

    METHOD = "POST"
    URL = "/singletask/add"
    URL_POST = "/singletask/add"
    ARGUMENTS = (["task", "arguments", "priority"],)

    HELP_SHORT = "Adds a single task to the database."
    HELP = """Adds a single task to the database (superusers only).

    Usage:
        ADD singletask <name>
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^singletask/add",
                AddSingleTaskCommand.as_view(),
                name="singletask_add",
            ),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return form for adding a single task."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        form = SingleTaskAPIForm()

        input = InputSerializer(form.as_dict(), self.URL_POST, form.get_order())
        return input.as_json

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Add single task."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        form = SingleTaskAPIForm(data)

        if form.is_valid():
            try:
                form.save()
            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

            return Message("Ok.").as_json

        return ErrorMessage("\n{}".format(format_cli_form_errors(form))).as_json  # type: ignore


class AddEnclosureCommand(BaseAPIView):

    METHOD = "POST"
    URL = "/enclosure/add"
    URL_POST = "/enclosure/add"
    ARGUMENTS = (["name", "platform", "netbox_id", "description", "is_virtual"],)

    HELP_SHORT = "Adds an enclosure to the database."
    HELP = """Adds an enclosure to the database (superusers only).

    Usage:
        ADD enclosure <name>
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^enclosure/add",
                AddEnclosureCommand.as_view(),
                name="enclosure_add",
            ),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return form for adding an enclosure."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        form = EnclosureAPIForm()

        input = InputSerializer(form.as_dict(), self.URL_POST, form.get_order())
        return input.as_json

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Add enclosure."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        form = EnclosureAPIForm(data)

        if form.is_valid():
            try:
                form.save()
            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

            return Message("Ok.").as_json

        return ErrorMessage("\n{}".format(format_cli_form_errors(form))).as_json  # type: ignore


class AddDomainArchitectureCommand(BaseAPIView):

    METHOD = "POST"
    URL = "/domainarchitecture/add"
    URL_POST = "/domainarchitecture/add"
    ARGUMENTS = (["domain", "arch", "contact_email"],)

    HELP_SHORT = "Adds a supported architecture entry for a domain."
    HELP = """Adds a supported architecture entry for a domain (superusers only).

    Usage:
        ADD domainarchitecture
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^domainarchitecture/add",
                AddDomainArchitectureCommand.as_view(),
                name="domainarchitecture_add",
            ),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return form for adding a supported architecture entry for a domain."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        form = DomainArchitectureAPIForm()

        input = InputSerializer(form.as_dict(), self.URL_POST, form.get_order())
        return input.as_json

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Add supported architecture entry for a domain."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        form = DomainArchitectureAPIForm(data)

        if form.is_valid():
            try:
                form.save()
            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

            return Message("Ok.").as_json

        return ErrorMessage("\n{}".format(format_cli_form_errors(form))).as_json  # type: ignore


class AddDomainCommand(BaseAPIView):

    METHOD = "POST"
    URL = "/domain/add"
    URL_POST = "/domain/add"
    ARGUMENTS = (
        [
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

    HELP_SHORT = "Adds a domain to the database."
    HELP = """Adds a domain to the database (superusers only).

    Usage:
        ADD domain <name>
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^domain/add",
                AddDomainCommand.as_view(),
                name="domain_add",
            ),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return form for adding a domain."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        form = DomainAPIForm()

        input = InputSerializer(form.as_dict(), self.URL_POST, form.get_order())
        return input.as_json

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Add domain."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        form = DomainAPIForm(data)

        if form.is_valid():
            try:
                form.save()
            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

            return Message("Ok.").as_json

        return ErrorMessage("\n{}".format(format_cli_form_errors(form))).as_json  # type: ignore


class AddNetworkInterfaceCommandGet(BaseAPIView):

    URL_POST = "/networkinterface/{fqdn}/add"

    HELP_SHORT = "Adds a network interface to a machine."
    HELP = """Adds a network interface to a machine (superusers only).

    Usage:
        ADD networkinterface <fqdn>
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^networkinterface/add",
                AddNetworkInterfaceCommandGet.as_view(),
                name="networkinterface_add_get",
            ),
        ]

    def get(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> Union[JsonResponse, HttpResponseRedirect]:
        """Return form for adding a network interface."""
        fqdn = request.GET.get("fqdn", "")
        try:
            result = get_machine(
                fqdn, redirect_to="api:networkinterface_add_get", data=request.GET
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

        form = NetworkInterfaceAPIForm()

        input = InputSerializer(
            form.as_dict(), self.URL_POST.format(fqdn=machine.fqdn), form.get_order()
        )
        return input.as_json


class AddNetworkInterfaceCommandPost(BaseAPIView):

    URL_POST = "/networkinterface/{fqdn}/add"

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^networkinterface/(?P<fqdn>[a-z0-9\.-]+)/add$",
                AddNetworkInterfaceCommandPost.as_view(),
                name="networkinterface_add_post",
            ),
        ]

    def post(
        self, request: Request, fqdn: str, *args: Any, **kwargs: Any
    ) -> Union[JsonResponse, HttpResponseRedirect]:
        """Add network interface to machine."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        try:
            result = get_machine(
                fqdn, redirect_to="api:networkinterface_add_post", data=request.GET
            )
            if isinstance(result, Serializer):
                return result.as_json
            elif isinstance(result, HttpResponseRedirect):
                return result
            machine = result
        except Exception as e:
            return ErrorMessage(str(e)).as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        form = NetworkInterfaceAPIForm(data)
        form.instance.machine = machine

        if form.is_valid():
            try:
                form.save()
            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

            return Message("Ok.").as_json

        return ErrorMessage("\n{}".format(format_cli_form_errors(form))).as_json  # type: ignore
