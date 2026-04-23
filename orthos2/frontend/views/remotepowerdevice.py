"""
All views that are under "/remote-power-devices".
"""
import logging
from typing import TYPE_CHECKING, Any, Dict

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import (
    Http404,
    HttpRequest,
    HttpResponse,
    HttpResponseBase,
    HttpResponseRedirect,
)
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from orthos2.data.models import Architecture, Domain, RemotePowerDevice, RemotePowerType
from orthos2.taskmanager import tasks
from orthos2.taskmanager.models import TaskManager
from orthos2.utils.misc import get_domain
from orthos2.utils.netbox import Netbox

if TYPE_CHECKING:
    from orthos2.types import AuthenticatedHttpRequest

logger = logging.getLogger("views")


class RemotePowerDevicesListView(PermissionRequiredMixin, ListView):
    model = RemotePowerDevice
    template_name = "frontend/remotepowerdevices/remotepowerdevices.html"
    paginate_by = 50
    permission_required = "data.change_remotepowerdevice"

    @method_decorator(login_required)
    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        return super(RemotePowerDevicesListView, self).dispatch(
            request, *args, **kwargs
        )

    def get_ordering(self) -> str:
        order_by = self.request.GET.get("order_by", None)
        order_direction = self.request.GET.get("order_direction", None)

        if order_by and order_direction in {"asc", "desc"}:
            ordering = (
                "{}".format(order_by)
                if order_direction == "desc"
                else "-{}".format(order_by)
            )
            return ordering
        return "fqdn"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Remote Power Devices"
        context["remotepowerdevices"] = RemotePowerDevice.objects.all()
        context["remotepowerdevices_list"] = self.object_list  # type: ignore
        return context


class RemotePowerDeviceDetailedEdit(PermissionRequiredMixin, UpdateView):
    model = RemotePowerDevice
    success_url = reverse_lazy("remote-power-device/<int:pk>")
    template_name = "frontend/remotepowerdevices/new_remotepowerdevice.html"
    success_url = reverse_lazy("frontend:remotepowerdevices")
    permission_required = "data.change_remotepowerdevice"

    fields = ["fqdn", "netbox_id", "username", "password", "url"]

    @method_decorator(login_required)
    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        return super(RemotePowerDeviceDetailedEdit, self).dispatch(
            request, *args, **kwargs
        )

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Remote Power Device"
        context["action"] = "edit"
        return context


class NewRemotePowerDevice(PermissionRequiredMixin, CreateView):
    model = RemotePowerDevice
    template_name = "frontend/remotepowerdevices/new_remotepowerdevice.html"
    success_url = reverse_lazy("frontend:remotepowerdevices")
    permission_required = "data.change_remotepowerdevice"

    fields = ["fqdn", "netbox_id", "username", "password", "url"]

    @method_decorator(login_required)
    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        return super(NewRemotePowerDevice, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        netbox = Netbox.get_instance()
        # Get domain from FQDN
        form.instance.domain = Domain.objects.get(name=get_domain(form.instance.fqdn))
        # Check if NetBox Device exists
        netbox_object = netbox.fetch_device(form.instance.netbox_id)
        logger.info(netbox_object)
        # Check FQDN and Device Name identical
        if netbox_object.get("name", "") != form.instance.fqdn:
            form.add_error(
                "fqdn", "NetBox Device Name and Orthos 2 FQDN not identical!"
            )
            return super().form_invalid(form)  # type: ignore
        # Fetch IPv4 and IPv6 from Primary IPs
        primary_ipv4_id = netbox_object.get("primary_ip4", {}).get("id", "")
        primary_ipv6_id = netbox_object.get("primary_ip6", {}).get("id", "")
        if not primary_ipv4_id and not primary_ipv6_id:
            form.add_error(
                "netbox_id",
                "Device needs at least IPv4 or IPv6 set as a primary IP in NetBox.",
            )
            return super().form_invalid(form)  # type: ignore
        if primary_ipv4_id:
            primary_ipv4 = netbox.fetch_ip(primary_ipv4_id)
        else:
            primary_ipv4 = {}
        if primary_ipv6_id:
            primary_ipv6 = netbox.fetch_ip(primary_ipv6_id)
        else:
            primary_ipv6 = {}
        # Check Primary IPv4 and Primary IPv6 belong to the same interface if both families are used.
        primary_interface = {}
        if primary_ipv4_id and primary_ipv6_id:
            if primary_ipv4.get("assigned_object", {}).get(
                "id", ""
            ) == primary_ipv6.get("assigned_object", {}).get("id", ""):
                primary_interface = netbox.fetch_interface(
                    primary_ipv4.get("assigned_object", {}).get("id", "")
                )
            else:
                form.add_error(
                    "netbox_id",
                    "Primary IPs must belong to the same interface in NetBox.",
                )
                return super().form_invalid(form)  # type: ignore
        elif primary_ipv4_id:
            primary_interface = netbox.fetch_interface(
                primary_ipv4.get("assigned_object", {}).get("id", "")
            )
        elif primary_ipv6_id:
            primary_interface = netbox.fetch_interface(
                primary_ipv6.get("assigned_object", {}).get("id", "")
            )
        # Fetch IPv4 and/or IPv6 address from NetBox
        if primary_ipv4:
            form.instance.ip_address_v4 = primary_ipv4.get("display", "").split("/")[0]
        if primary_ipv6:
            form.instance.ip_address_v6 = primary_ipv6.get("display", "").split("/")[0]
        # Fetch MAC from Network Interface with primary IPs
        primary_mac = primary_interface.get("primary_mac_address")
        if primary_mac is not None:
            form.instance.mac = primary_mac.get("display", "")
        else:
            form.add_error(
                "netbox_id",
                "Device in NetBox doesn't have an interface with a primary MAC address.",
            )
            return super().form_invalid(form)  # type: ignore
        # Fetch Fence Agent from Network Interface with primary IPs
        try:
            form.instance.fence_agent = RemotePowerType.objects.get(
                name=primary_interface.get("custom_fields", {}).get("fence_agent", "")
            )
        except RemotePowerType.DoesNotExist:
            form.add_error(
                "netbox_id",
                "Device in NetBox doesn't have a valid fence agent set on its primary interface.",
            )
            return super().form_invalid(form)  # type: ignore
        # Fetch architecture from NetBox
        remotepowerdevice_arch = netbox_object.get("custom_fields", {}).get("arch")
        if remotepowerdevice_arch is None:
            form.add_error(
                "netbox_id",
                "Machine doesn't have a CPU Architecture set in NetBox.",
            )
            return super().form_invalid(form)  # type: ignore
        form.instance.architecture = Architecture.objects.get(
            name=remotepowerdevice_arch
        )
        logger.info(form.instance)
        return super().form_valid(form)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "New Remote Power Device"
        context["action"] = "new"
        return context


class DeleteRemotePowerDevice(PermissionRequiredMixin, DeleteView):  # type: ignore
    model = RemotePowerDevice
    template_name = (
        "frontend/remotepowerdevices/remotepowerdevice_confirm_deletion.html"
    )
    success_url = reverse_lazy("frontend:remotepowerdevices")
    permission_required = "data.change_remotepowerdevice"

    @method_decorator(login_required)
    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        return super(DeleteRemotePowerDevice, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Delete Remote Power Device"
        return context


@login_required
@permission_required("data.change_remotepowerdevice")
def remotepowerdevice_detail(request: HttpRequest, id: int) -> HttpResponse:
    try:
        remotepowerdevice = RemotePowerDevice.objects.get(pk=id)
        return render(
            request,
            "frontend/remotepowerdevices/detail/overview.html",
            {
                "remotepowerdevice": remotepowerdevice,
                "title": f"Remote Power Device {remotepowerdevice.fqdn}",
            },
        )
    except RemotePowerDevice.DoesNotExist:
        raise Http404("Remote Power Device does not exist")


@login_required
def remotepowerdevice_fetch_netbox(
    request: HttpRequest, id: int
) -> HttpResponseRedirect:
    try:
        requested_remotepowerdevice = RemotePowerDevice.objects.get(pk=id)
    except RemotePowerDevice.DoesNotExist:
        messages.error(request, "Remote Power Device does not exist!")
        return redirect("frontend:remotepowerdevices")

    try:
        TaskManager.add(
            tasks.NetboxFetchRemotePowerDevice(requested_remotepowerdevice.pk)
        )
        messages.info(
            request,
            "Fetching data from Netbox for remote power device - this can take some seconds...",
        )
    except Exception as exception:
        messages.error(request, exception)  # type: ignore

    return redirect("frontend:remotepowerdevice_detail", id=id)


@login_required
def remotepowerdevice_netboxcomparison(
    request: "AuthenticatedHttpRequest", id: int
) -> HttpResponseBase:
    perm_list = [
        "data.view_remotepowerdevice",
    ]
    if not request.user.has_perms(perm_list):
        messages.error(request, "Not enough user permissions.")
        return redirect("remotepowerdevices")

    try:
        remotepowerdevice = RemotePowerDevice.objects.get(pk=id)
    except RemotePowerDevice.DoesNotExist:
        messages.error(request, "Remote Power Device does not exist.")
        return redirect("frontend:remotepowerdevices")

    if remotepowerdevice.netboxorthoscomparisionruns.count() > 0:
        remotepowerdevice_run = remotepowerdevice.netboxorthoscomparisionruns.latest(
            "compare_timestamp"
        )
    else:
        remotepowerdevice_run = None

    return render(
        request,
        "frontend/remotepowerdevices/detail/netbox_comparison.html",
        {
            "remotepowerdevice": remotepowerdevice,
            "title": "Netbox Comparison",
            "remotepowerdevice_run": remotepowerdevice_run,
        },
    )


@login_required
def remotepowerdevice_compare_netbox(
    request: HttpRequest, id: int
) -> HttpResponseRedirect:
    try:
        requested_remotepowerdevice = RemotePowerDevice.objects.get(pk=id)
    except RemotePowerDevice.DoesNotExist:
        messages.error(request, "Remote Power Device does not exist!")
        return redirect("frontend:remotepowerdevices")

    try:
        TaskManager.add(
            tasks.NetboxCompareRemotePowerDevice(requested_remotepowerdevice.pk)
        )
        messages.info(
            request,
            "Comparing data with Netbox - this can take some seconds...",
        )
    except Exception as exception:
        messages.error(request, exception)  # type: ignore

    return redirect("frontend:remotepowerdevice_detail", id=id)
