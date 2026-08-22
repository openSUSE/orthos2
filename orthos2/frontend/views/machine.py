"""
All views that are related to "/machine".
"""

import logging
from typing import TYPE_CHECKING, Any, Dict, Set, Union

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import (
    Http404,
    HttpRequest,
    HttpResponse,
    HttpResponseBase,
    HttpResponsePermanentRedirect,
    HttpResponseRedirect,
)
from django.shortcuts import get_object_or_404, redirect, render  # type: ignore
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, UpdateView

from orthos2.data.models import (
    BMC,
    Annotation,
    Machine,
    NetworkInterface,
    RemotePower,
    SerialConsole,
)
from orthos2.data.models.netboxorthoscomparision import NetboxOrthosComparisionRun
from orthos2.frontend.decorators import check_permissions
from orthos2.frontend.forms.addmachine import AddMachineFormView
from orthos2.frontend.forms.reservemachine import ReserveMachineForm
from orthos2.frontend.forms.setupmachine import SetupMachineForm
from orthos2.frontend.forms.virtualmachine import VirtualMachineForm
from orthos2.frontend.mixins import SuperuserRequiredMixin
from orthos2.taskmanager import tasks
from orthos2.taskmanager.models import TaskManager
from orthos2.utils.cobbler import CobblerServer
from orthos2.utils.misc import add_offset_to_date

if TYPE_CHECKING:
    from orthos2.types import AuthenticatedHttpRequest

logger = logging.getLogger("views")


def _collect_cobbler_diff(host: Machine) -> dict[str, Set[str]]:
    """
    Method is called after the machine was checked for being a Cobbler Server. As such it has at least one domain.
    """
    target_domains = host.cobbler_server_for.all()
    result = {}

    # Create the Cobbler XML-RPC Server object with the first domain to reduce the XML-RPC calls needed.
    cobbler_server = CobblerServer(target_domains[0])
    cobbler_systems = set(cobbler_server.get_machines())
    for domain in target_domains:
        logger.info(domain.name)
        domain_suffix = "." + domain.name
        domain_orthos_fqdns = set(
            domain.machine_set.exclude(active=False).values_list("fqdn", flat=True)
        )
        cobbler_scoped_systems = {
            fqdn for fqdn in cobbler_systems if fqdn.endswith(domain_suffix)
        }
        result[domain.name] = cobbler_scoped_systems - domain_orthos_fqdns

    result["unscoped"] = set()
    for fqdn in cobbler_systems:
        if not any(fqdn.endswith(domain.name) for domain in target_domains):
            result["unscoped"].add(fqdn)

    return result


@login_required
def pci(request: HttpRequest, id: int) -> HttpResponse:
    try:
        machine = Machine.objects.get(pk=id)
        return render(
            request,
            "frontend/machines/detail/pci.html",
            {"machine": machine, "title": "lspci"},
        )
    except Machine.DoesNotExist:
        raise Http404("Machine does not exist")


@login_required
def cpu(request: HttpRequest, id: int) -> HttpResponse:
    try:
        machine = Machine.objects.get(pk=id)
        return render(
            request,
            "frontend/machines/detail/cpu.html",
            {"machine": machine, "title": "CPU"},
        )
    except Machine.DoesNotExist:
        raise Http404("Machine does not exist")


@login_required
def networkinterfaces(request: HttpRequest, id: int) -> HttpResponse:
    try:
        machine = Machine.objects.get(pk=id)
        return render(
            request,
            "frontend/machines/detail/networkinterfaces.html",
            {"machine": machine, "title": "Network Interfaces"},
        )
    except Machine.DoesNotExist:
        raise Http404("Machine does not exist")


@login_required
def serialconsole(request: HttpRequest, id: int) -> HttpResponse:
    try:
        machine = Machine.objects.get(pk=id)
        return render(
            request,
            "frontend/machines/detail/serialconsole.html",
            {"machine": machine, "title": "Serial Console"},
        )
    except Machine.DoesNotExist:
        raise Http404("Machine does not exist")


@login_required
def remotepower(request: HttpRequest, id: int) -> HttpResponse:
    try:
        machine = Machine.objects.get(pk=id)
        return render(
            request,
            "frontend/machines/detail/remotepower.html",
            {"machine": machine, "title": "Remote Power"},
        )
    except Machine.DoesNotExist:
        raise Http404("Machine does not exist")


@login_required
def installations(request: HttpRequest, id: int) -> HttpResponse:
    try:
        machine = Machine.objects.get(pk=id)
        return render(
            request,
            "frontend/machines/detail/installations.html",
            {"machine": machine, "title": "Installations"},
        )
    except Machine.DoesNotExist:
        raise Http404("Machine does not exist")


@login_required
def usb(request: HttpRequest, id: int) -> HttpResponse:
    try:
        machine = Machine.objects.get(pk=id)
        return render(
            request,
            "frontend/machines/detail/usb.html",
            {"machine": machine, "title": "USB"},
        )
    except Machine.DoesNotExist:
        raise Http404("Machine does not exist")


@login_required
def scsi(request: HttpRequest, id: int) -> HttpResponse:
    try:
        machine = Machine.objects.get(pk=id)
        return render(
            request,
            "frontend/machines/detail/scsi.html",
            {"machine": machine, "title": "SCSI"},
        )
    except Machine.DoesNotExist:
        raise Http404("Machine does not exist")


@login_required
def virtualization(request: HttpRequest, id: int) -> HttpResponse:
    try:
        machine = Machine.objects.get(pk=id)
    except Machine.DoesNotExist:
        raise Http404("Machine does not exist")

    if machine.virtualization_api is None:
        return HttpResponse(status=501, content="No virtualization API available!")

    return render(
        request,
        "frontend/machines/detail/virtualization.html",
        {"machine": machine, "title": "Virtualization"},
    )


@login_required
def virtualization_add(
    request: HttpRequest, id: int
) -> Union[HttpResponsePermanentRedirect, HttpResponseRedirect, HttpResponse]:
    try:
        machine = Machine.objects.get(pk=id)
    except Machine.DoesNotExist:
        raise Http404("Machine does not exist")

    if machine.virtualization_api is None:
        return HttpResponse(status=501, content="No virtualization API available!")

    if request.method == "GET":
        form = VirtualMachineForm(virtualization_api=machine.virtualization_api)

    else:
        form = VirtualMachineForm(
            request.POST, virtualization_api=machine.virtualization_api
        )
        if form.is_valid():
            vm = None
            try:
                vm = machine.virtualization_api.create(**form.cleaned_data)

                vm.reserve(
                    reason="VM of {}".format(request.user),
                    until=add_offset_to_date(30),  # type: ignore
                    user=request.user,  # type: ignore
                )
                messages.success(
                    request, "Virtual machine '{}' created.".format(vm.fqdn)
                )

                return redirect("frontend:detail", id=vm.pk)

            except Exception as exception:
                logger.exception(exception)
                messages.error(request, exception)  # type: ignore
                if vm:
                    vm.delete()
                return redirect("frontend:machines")

    return render(
        request,
        "frontend/machines/detail/virtualization_add.html",
        {"form": form, "machine": machine, "title": "Virtualization"},
    )


@login_required
def misc(request: HttpRequest, id: int) -> HttpResponse:
    try:
        machine = Machine.objects.get(pk=id)
        return render(
            request,
            "frontend/machines/detail/miscellaneous.html",
            {"machine": machine, "title": "Miscellaneous"},
        )
    except Machine.DoesNotExist:
        raise Http404("Machine does not exist")


@login_required
@check_permissions()
def machine_reserve(
    request: HttpRequest, id: int
) -> Union[HttpResponsePermanentRedirect, HttpResponseRedirect, HttpResponse]:
    try:
        machine = Machine.objects.get(pk=id)
    except Machine.DoesNotExist:
        messages.error(request, "Machine does not exist!")
        return redirect("fronted:machines")

    if request.method == "GET":
        form = ReserveMachineForm(
            reason=machine.reserved_reason,
            until=machine.reserved_until,
            permanently=machine.reserved_permanently,
        )

    else:
        form = ReserveMachineForm(request.POST)

        if form.is_valid():
            reason = form.cleaned_data["reason"]
            until = form.cleaned_data["until"]

            try:
                machine.reserve(reason, until, user=request.user)  # type: ignore
                messages.success(request, "Machine successfully reserved.")
            except Exception as exception:
                messages.error(request, exception)  # type: ignore

            return redirect("frontend:detail", id=id)

    return render(
        request,
        "frontend/machines/reserve.html",
        {"form": form, "machine": machine, "title": "Reserve Machine"},
    )


@login_required
@check_permissions()
def machine_release(request: HttpRequest, id: int) -> HttpResponseRedirect:
    try:
        machine = Machine.objects.get(pk=id)

        try:
            machine.release(user=request.user)
            messages.success(request, "Machine successfully released.")

            if machine.is_virtual_machine():
                if machine.hypervisor and (
                    machine.hypervisor.virtualization_api is not None
                ):
                    return redirect("frontend:machines")

        except Exception as exception:
            logger.exception(exception)
            messages.error(request, exception)  # type: ignore

        return redirect("frontend:detail", id=id)

    except Machine.DoesNotExist:
        messages.error(request, "Machine does not exist!")
        return redirect("frontend:machines")


@login_required
def history(
    request: HttpRequest, id: int
) -> Union[HttpResponsePermanentRedirect, HttpResponseRedirect, HttpResponse]:
    try:
        machine = Machine.objects.get(pk=id)
        return render(
            request,
            "frontend/machines/detail/history.html",
            {"machine": machine, "title": "Reservation History"},
        )
    except Machine.DoesNotExist:
        messages.error(request, "Machine does not exist!")
        return redirect("forntend:machines")


@login_required
@check_permissions()
def rescan(request: HttpRequest, id: int) -> HttpResponseRedirect:
    try:
        machine = Machine.objects.get(pk=id)
    except Machine.DoesNotExist:
        messages.error(request, "Machine does not exist!")
        return redirect("frontend:machines")

    if request.GET.get("action"):
        try:
            machine.scan(request.GET.get("action"))  # type: ignore
            messages.info(request, "Rescanning machine - this can take some seconds...")
        except Exception as exception:
            messages.error(request, exception)  # type: ignore

    return redirect("frontend:detail", id=id)


@login_required
@check_permissions()
def setup(
    request: HttpRequest, id: int
) -> Union[HttpResponsePermanentRedirect, HttpResponseRedirect, HttpResponse]:
    try:
        machine = Machine.objects.get(pk=id)
    except Machine.DoesNotExist:
        messages.error(request, "Machine does not exist!")
        return redirect("frontend:machines")

    if request.method == "GET":
        if not machine.has_remotepower():
            messages.warning(
                request,
                "This machine has no remote power - a manuall reboot may be required.",
            )
        form = SetupMachineForm(machine=machine)

    else:

        form = SetupMachineForm(request.POST, machine=machine)

        if form.is_valid():
            choice = form.cleaned_data["setup"]

            valid = machine.fqdn_domain.is_valid_setup_choice(
                choice, machine.architecture.name
            )
            if not valid:
                messages.error(request, "Unknown choice '{}'!".format(choice))
                return redirect("frontend:detail", id=id)

            try:
                result = machine.setup(choice)

                if result:
                    from orthos2.utils.distribution import (
                        is_manual_installation,
                        is_risky_sles_version,
                        needs_boot_order_warning,
                    )

                    messages.success(request, "Setup '{}' initialized.".format(choice))

                    if needs_boot_order_warning(choice):
                        warning_msg = "Note: "
                        if is_risky_sles_version(choice):
                            warning_msg += "This SLES version may require manual BIOS/UEFI boot order configuration. "
                        if is_manual_installation(choice):
                            warning_msg += (
                                "Manual installation requires setting boot order after OS installation "
                                "completes."
                            )

                        messages.warning(request, warning_msg)
                else:
                    messages.warning(
                        request,
                        "Machine has no setup capability! Please contact '{}'.".format(
                            machine.get_support_contact()
                        ),
                    )

            except Exception as exception:
                messages.error(request, exception)  # type: ignore

        return redirect("frontend:detail", id=id)

    return render(
        request,
        "frontend/machines/setup.html",
        {"form": form, "machine": machine, "title": "Setup Machine"},
    )


@login_required
def cobbler_cleanup(request: HttpRequest, id: int) -> HttpResponse:
    try:
        target_machine = Machine.objects.get(pk=id)
    except Machine.DoesNotExist:
        messages.error(request, "Machine does not exist")
        raise Http404("Machine does not exist")

    if not target_machine.is_cobbler_server():
        messages.error(request, "Machine is not a cobbler server")
        return redirect("frontend:detail", id=id)

    if request.method == "POST":
        selected_fqdns = set(request.POST.getlist("fqdn"))
        diff = _collect_cobbler_diff(target_machine)

        # Flatten the diff values to a single set of allowed FQDNs
        allowed_fqdns = set()
        for fqdns in diff.values():
            allowed_fqdns.update(fqdns)

        if selected_fqdns:
            target_domains = target_machine.cobbler_server_for.all()
            cobbler_server = CobblerServer(target_domains[0])

            fqdn_delete_success = set()
            for fqdn in selected_fqdns:
                if fqdn in allowed_fqdns:
                    cobbler_server.remove_by_name(fqdn)
                    fqdn_delete_success.add(fqdn)

            messages.success(
                request,
                "Deleted {count} machine(s) from Cobbler".format(
                    count=len(fqdn_delete_success)
                ),
            )
        else:
            messages.warning(request, "No machines selected for deletion.")

        return redirect("frontend:cleanup_domain_cobbler_page", id=id)

    diff = _collect_cobbler_diff(target_machine)
    return render(
        request,
        "frontend/machines/detail/cobbler_cleanup.html",
        {
            "machine": target_machine,
            "title": "Cobbler Cleanup",
            "diff": diff,
        },
    )


@login_required
@check_permissions()
def machine(request: HttpRequest, id: int) -> HttpResponse:
    try:
        machine = Machine.objects.get(pk=id)
    except Machine.DoesNotExist:
        messages.error(request, "Machine does not exist.")
        return redirect("frontend:machines")

    return render(
        request,
        "frontend/machines/detail/overview.html",
        {"machine": machine, "title": "Machine"},
    )


@login_required
def machine_netboxcomparision(
    request: "AuthenticatedHttpRequest", id: int
) -> HttpResponseBase:
    perm_list = [
        "data.view_machine",
    ]
    if not request.user.has_perms(perm_list):
        messages.error(request, "Not enough user permissions.")
        return redirect("frontend:machines")

    try:
        machine = Machine.objects.get(pk=id)
    except Machine.DoesNotExist:
        messages.error(request, "Machine does not exist.")
        return redirect("frontend:machines")

    if machine.netboxorthoscomparisionruns.count() > 0:
        machine_run = machine.netboxorthoscomparisionruns.latest("compare_timestamp")
    else:
        machine_run = None
    if machine.has_bmc() and machine.bmc.netboxorthoscomparisionruns.count() > 0:
        bmc_run = machine.bmc.netboxorthoscomparisionruns.latest("compare_timestamp")
    else:
        bmc_run = None
    network_interface_run: Dict[str, NetboxOrthosComparisionRun] = {}
    for intf in machine.networkinterfaces.all():
        network_interface_runs = NetboxOrthosComparisionRun.objects.filter(
            object_network_interface=intf
        )
        if network_interface_runs.count() == 0:
            continue
        network_interface_run[intf.name] = network_interface_runs.latest(
            "compare_timestamp"
        )

    return render(
        request,
        "frontend/machines/detail/netboxcomparison.html",
        {
            "machine": machine,
            "title": "Netbox Comparison",
            "bmc_run": bmc_run if machine.has_bmc() else None,
            "network_interface_run": network_interface_run,
            "machine_run": machine_run,
        },
    )


@login_required
@check_permissions()
def fetch_netbox(request: HttpRequest, id: int) -> HttpResponseRedirect:
    try:
        requested_machine = Machine.objects.get(pk=id)
    except Machine.DoesNotExist:
        messages.error(request, "Machine does not exist!")
        return redirect("frontend:machines")

    if requested_machine.netbox_id == 0:
        messages.error(request, "Machine is not linked to NetBox!")
        return redirect("frontend:detail", id=id)

    try:
        TaskManager.add(tasks.NetboxFetchFullMachine(requested_machine.pk))
        messages.info(
            request,
            "Fetching data from Netbox for machine - this can take some seconds...",
        )
    except Exception as exception:
        messages.error(request, exception)  # type: ignore

    return redirect("frontend:detail", id=id)


@login_required
@check_permissions()
def compare_netbox(request: HttpRequest, id: int) -> HttpResponseRedirect:
    try:
        requested_machine = Machine.objects.get(pk=id)
    except Machine.DoesNotExist:
        messages.error(request, "Machine does not exist!")
        return redirect("frontend:machines")

    if requested_machine.netbox_id == 0:
        messages.error(request, "Machine is not linked to NetBox!")
        return redirect("frontend:detail", id=id)

    try:
        TaskManager.add(tasks.NetboxCompareFullMachine(requested_machine.pk))
        messages.info(
            request,
            "Comparing data with Netbox - this can take some seconds...",
        )
    except Exception as exception:
        messages.error(request, exception)  # type: ignore

    return redirect("frontend:detail", id=id)


@login_required
def machine_add(request: "AuthenticatedHttpRequest") -> HttpResponseBase:
    perm_list = [
        "data.add_machine",
        "data.add_bmc",
        "data.add_remotepower",
        "data.add_networkinterface",
    ]
    if not request.user.has_perms(perm_list):
        messages.error(request, "Insufficient user permissions.")
        return redirect("frontend:machines")

    return AddMachineFormView.as_view()(request)


class DeleteNetworkInterface(DeleteView):  # type: ignore
    model = NetworkInterface
    template_name = "frontend/machines/detail/networkinterface_confirm_deletion.html"

    def get_success_url(self) -> str:
        return reverse_lazy(  # type: ignore
            "frontend:networkinterfaces", kwargs={"id": self.object.machine_id}
        )

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        if not request.user.is_authenticated:
            return redirect("frontend:login")
        if not request.user.is_superuser:  # type: ignore
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form: Any) -> HttpResponse:
        obj = self.get_object()
        if obj.primary:
            raise PermissionDenied
        return super().form_valid(form)


NETWORKINTERFACE_FIELDS = ["primary", "mac_address", "ip_address_v4", "ip_address_v6"]


class NewNetworkInterface(SuperuserRequiredMixin, CreateView):
    model = NetworkInterface
    template_name = "frontend/machines/detail/new_networkinterface.html"
    fields = NETWORKINTERFACE_FIELDS

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Any:
        self.machine = get_object_or_404(Machine, pk=self.kwargs["machine_id"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self) -> Dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = NetworkInterface(machine=self.machine)
        return kwargs

    def get_success_url(self) -> str:
        return reverse_lazy(
            "frontend:networkinterfaces", kwargs={"id": self.machine.pk}
        )

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["machine"] = self.machine
        context["title"] = "New Network Interface for {}".format(self.machine.fqdn)
        context["action"] = "new"
        return context


class NetworkInterfaceDetailedEdit(SuperuserRequiredMixin, UpdateView):
    model = NetworkInterface
    template_name = "frontend/machines/detail/new_networkinterface.html"
    fields = NETWORKINTERFACE_FIELDS

    def get_success_url(self) -> str:
        return reverse_lazy(
            "frontend:networkinterfaces", kwargs={"id": self.object.machine_id}
        )

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["machine"] = self.object.machine
        context["title"] = "Edit Network Interface for {}".format(
            self.object.machine.fqdn
        )
        context["action"] = "edit"
        return context


BMC_FIELDS = [
    "fqdn",
    "mac",
    "username",
    "password",
    "fence_agent",
    "ip_address_v4",
    "ip_address_v6",
]


class NewBMC(SuperuserRequiredMixin, CreateView):
    model = BMC
    template_name = "frontend/machines/detail/new_bmc.html"
    fields = BMC_FIELDS

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Any:
        self.machine = get_object_or_404(Machine, pk=self.kwargs["machine_id"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self) -> Dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = BMC(machine=self.machine)
        return kwargs

    def get_success_url(self) -> str:
        return reverse_lazy(
            "frontend:networkinterfaces", kwargs={"id": self.machine.pk}
        )

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["machine"] = self.machine
        context["title"] = "New BMC for {}".format(self.machine.fqdn)
        context["action"] = "new"
        return context


class BMCDetailedEdit(SuperuserRequiredMixin, UpdateView):
    model = BMC
    template_name = "frontend/machines/detail/new_bmc.html"
    fields = BMC_FIELDS

    def get_success_url(self) -> str:
        return reverse_lazy(
            "frontend:networkinterfaces", kwargs={"id": self.object.machine_id}
        )

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["machine"] = self.object.machine
        context["title"] = "Edit BMC for {}".format(self.object.machine.fqdn)
        context["action"] = "edit"
        return context


class DeleteBMC(SuperuserRequiredMixin, DeleteView):  # type: ignore
    model = BMC
    template_name = "frontend/machines/detail/bmc_confirm_deletion.html"

    def get_success_url(self) -> str:
        return reverse_lazy(
            "frontend:networkinterfaces", kwargs={"id": self.object.machine_id}
        )

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Delete BMC"
        return context


SERIALCONSOLE_FIELDS = [
    "stype",
    "baud_rate",
    "kernel_device",
    "kernel_device_num",
    "console_server",
    "port",
    "command",
    "comment",
]


class NewSerialConsole(SuperuserRequiredMixin, CreateView):
    model = SerialConsole
    template_name = "frontend/machines/detail/new_serialconsole.html"
    fields = SERIALCONSOLE_FIELDS

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Any:
        self.machine = get_object_or_404(Machine, pk=self.kwargs["machine_id"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self) -> Dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = SerialConsole(machine=self.machine)
        return kwargs

    def get_success_url(self) -> str:
        return reverse_lazy("frontend:serialconsole", kwargs={"id": self.machine.pk})

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["machine"] = self.machine
        context["title"] = "New Serial Console for {}".format(self.machine.fqdn)
        context["action"] = "new"
        return context


class SerialConsoleDetailedEdit(SuperuserRequiredMixin, UpdateView):
    model = SerialConsole
    template_name = "frontend/machines/detail/new_serialconsole.html"
    fields = SERIALCONSOLE_FIELDS

    def get_success_url(self) -> str:
        return reverse_lazy(
            "frontend:serialconsole", kwargs={"id": self.object.machine_id}
        )

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["machine"] = self.object.machine
        context["title"] = "Edit Serial Console for {}".format(self.object.machine.fqdn)
        context["action"] = "edit"
        return context


class DeleteSerialConsole(SuperuserRequiredMixin, DeleteView):  # type: ignore
    model = SerialConsole
    template_name = "frontend/machines/detail/serialconsole_confirm_deletion.html"

    def get_success_url(self) -> str:
        return reverse_lazy(
            "frontend:serialconsole", kwargs={"id": self.object.machine_id}
        )

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Delete Serial Console"
        return context


REMOTEPOWER_FIELDS = [
    "fence_agent",
    "remote_power_device",
    "port",
    "comment",
    "options",
]


class NewRemotePower(SuperuserRequiredMixin, CreateView):
    model = RemotePower
    template_name = "frontend/machines/detail/new_remotepower.html"
    fields = REMOTEPOWER_FIELDS

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Any:
        self.machine = get_object_or_404(Machine, pk=self.kwargs["machine_id"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self) -> Dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = RemotePower(machine=self.machine)
        return kwargs

    def get_success_url(self) -> str:
        return reverse_lazy("frontend:remotepower", kwargs={"id": self.machine.pk})

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["machine"] = self.machine
        context["title"] = "New Remote Power for {}".format(self.machine.fqdn)
        context["action"] = "new"
        return context

    def form_valid(self, form: Any) -> HttpResponse:
        try:
            return super().form_valid(form)
        except ValidationError as e:
            form.add_error(None, e)
            return self.form_invalid(form)


class RemotePowerDetailedEdit(SuperuserRequiredMixin, UpdateView):
    model = RemotePower
    template_name = "frontend/machines/detail/new_remotepower.html"
    fields = REMOTEPOWER_FIELDS

    def get_success_url(self) -> str:
        return reverse_lazy(
            "frontend:remotepower", kwargs={"id": self.object.machine_id}
        )

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["machine"] = self.object.machine
        context["title"] = "Edit Remote Power for {}".format(self.object.machine.fqdn)
        context["action"] = "edit"
        return context

    def form_valid(self, form: Any) -> HttpResponse:
        try:
            return super().form_valid(form)
        except ValidationError as e:
            form.add_error(None, e)
            return self.form_invalid(form)


class DeleteRemotePower(SuperuserRequiredMixin, DeleteView):  # type: ignore
    model = RemotePower
    template_name = "frontend/machines/detail/remotepower_confirm_deletion.html"

    def get_success_url(self) -> str:
        return reverse_lazy(
            "frontend:remotepower", kwargs={"id": self.object.machine_id}
        )

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Delete Remote Power"
        return context


class DeleteAnnotation(SuperuserRequiredMixin, DeleteView):  # type: ignore
    model = Annotation
    template_name = "frontend/machines/detail/annotation_confirm_deletion.html"

    def get_success_url(self) -> str:
        return reverse_lazy("frontend:detail", kwargs={"id": self.object.machine_id})

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Delete Annotation"
        return context


MACHINE_FIELDS = [
    "fqdn",
    "enclosure",
    "architecture",
    "system",
    "serial_number",
    "product_code",
    "comment",
    "device_type",
    "contact_email",
    "kernel_options",
    "netbox_id",
    "administrative",
    "nda",
    "autoreinstall",
    "active",
    "vm_dedicated_host",
    "vm_auto_delete",
    "vm_max",
    "virt_api_int",
    "hypervisor",
    "check_connectivity",
    "collect_system_information",
    "tftp_server",
    "dhcp_filename",
]


class MachineDetailedEdit(SuperuserRequiredMixin, UpdateView):
    model = Machine
    template_name = "frontend/machines/detail/edit_machine.html"
    fields = MACHINE_FIELDS

    def get_success_url(self) -> str:
        return reverse_lazy("frontend:detail", kwargs={"id": self.object.pk})

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["machine"] = self.object
        context["title"] = "Edit Machine {}".format(self.object.fqdn)
        return context

    def form_valid(self, form: Any) -> HttpResponse:
        try:
            return super().form_valid(form)
        except ValidationError as e:
            form.add_error(None, e)
            return self.form_invalid(form)
