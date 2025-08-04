"""
All views that are related to "/machine".
"""

import logging
from typing import TYPE_CHECKING, Dict, Union

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import (
    Http404,
    HttpRequest,
    HttpResponse,
    HttpResponseBase,
    HttpResponsePermanentRedirect,
    HttpResponseRedirect,
)
from django.shortcuts import redirect, render  # type: ignore

from orthos2.data.models import Machine, ServerConfig
from orthos2.data.models.netboxorthoscomparision import NetboxOrthosComparisionRun
from orthos2.frontend.decorators import check_permissions
from orthos2.frontend.forms.addmachine import AddMachineFormView
from orthos2.frontend.forms.reservemachine import ReserveMachineForm
from orthos2.frontend.forms.setupmachine import SetupMachineForm
from orthos2.frontend.forms.virtualmachine import VirtualMachineForm
from orthos2.taskmanager import tasks
from orthos2.taskmanager.models import TaskManager
from orthos2.utils.misc import add_offset_to_date

if TYPE_CHECKING:
    from orthos2.types import AuthenticatedHttpRequest

logger = logging.getLogger("views")


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
            reason=machine.reserved_reason, until=machine.reserved_until
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
                    messages.success(request, "Setup '{}' initialized.".format(choice))
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
def console(request: HttpRequest, id: int) -> HttpResponse:
    try:
        machine = Machine.objects.get(pk=id)
        return render(
            request,
            "frontend/machines/detail/console.html",
            {
                "machine": machine,
                "port": ServerConfig.get_server_config_manager().by_key(
                    "websocket.cscreen.port"
                ),
                "title": "Serial Console",
            },
        )
    except Machine.DoesNotExist:
        raise Http404("Machine does not exist")


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
