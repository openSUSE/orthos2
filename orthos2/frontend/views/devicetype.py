"""
All views that are under "/devicetypes".
"""

from typing import Any, Dict, List

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q, QuerySet
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

from orthos2.data.models import DeviceType
from orthos2.frontend.forms.devicetype import DeviceTypeForm
from orthos2.frontend.mixins import SuperuserRequiredMixin
from orthos2.taskmanager import tasks
from orthos2.taskmanager.models import TaskManager


class DeviceTypeListView(ListView):
    model = DeviceType
    template_name = "frontend/devicetypes/devicetypes.html"
    paginate_by = 50

    # login is required, but any authenticated user may view the list
    @method_decorator(login_required)
    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet["DeviceType"]:
        filters: List[Q] = []

        if self.request.GET.get("query"):
            filters.append(Q(name__contains=self.request.GET.get("query")))

        has_netbox = self.request.GET.get("has_netbox")
        if has_netbox == "1":
            filters.append(Q(netbox_id__gt=0))
        elif has_netbox == "0":
            filters.append(Q(netbox_id=0))

        return super().get_queryset().filter(*filters)  # type: ignore

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
        return "name"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Device Types"
        return context


class NewDeviceType(SuperuserRequiredMixin, CreateView):
    model = DeviceType
    template_name = "frontend/devicetypes/new_devicetype.html"
    success_url = reverse_lazy("frontend:devicetypes")
    form_class = DeviceTypeForm

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "New Device Type"
        context["action"] = "new"
        return context


class DeviceTypeDetailedEdit(SuperuserRequiredMixin, UpdateView):
    model = DeviceType
    template_name = "frontend/devicetypes/new_devicetype.html"
    success_url = reverse_lazy("frontend:devicetypes")
    form_class = DeviceTypeForm

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Device Type"
        context["action"] = "edit"
        return context


class DeleteDeviceType(SuperuserRequiredMixin, DeleteView):  # type: ignore
    model = DeviceType
    template_name = "frontend/devicetypes/devicetype_confirm_deletion.html"
    success_url = reverse_lazy("frontend:devicetypes")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Delete Device Type"
        return context


@login_required
def devicetype_detail(request: HttpRequest, id: int) -> HttpResponse:
    try:
        devicetype = DeviceType.objects.get(pk=id)
    except DeviceType.DoesNotExist:
        raise Http404("Device Type does not exist")

    return render(
        request,
        "frontend/devicetypes/detail/overview.html",
        {"devicetype": devicetype, "title": "Device Type {}".format(devicetype.name)},
    )


@login_required
def devicetype_fetch_netbox(request: HttpRequest, id: int) -> HttpResponseRedirect:
    if not request.user.is_superuser:  # type: ignore
        raise PermissionDenied

    try:
        requested_devicetype = DeviceType.objects.get(pk=id)
    except DeviceType.DoesNotExist:
        messages.error(request, "Device Type does not exist!")
        return redirect("frontend:devicetypes")

    if requested_devicetype.netbox_id == 0:
        messages.error(request, "Device Type is not linked to NetBox!")
        return redirect("frontend:devicetype_detail", id=id)

    try:
        TaskManager.add(tasks.NetboxFetchFullDeviceType(requested_devicetype.pk))
        messages.info(
            request,
            "Fetching data from Netbox for device type - this can take some seconds...",
        )
    except Exception as exception:
        messages.error(request, exception)  # type: ignore

    return redirect("frontend:devicetype_detail", id=id)


@login_required
def devicetype_netboxcomparison(request: HttpRequest, id: int) -> HttpResponse:
    try:
        devicetype = DeviceType.objects.get(pk=id)
    except DeviceType.DoesNotExist:
        raise Http404("Device Type does not exist")

    if devicetype.netboxorthoscomparisionruns.count() > 0:
        devicetype_run = devicetype.netboxorthoscomparisionruns.latest(
            "compare_timestamp"
        )
    else:
        devicetype_run = None

    return render(
        request,
        "frontend/devicetypes/detail/netbox_comparison.html",
        {
            "devicetype": devicetype,
            "title": "Netbox Comparison",
            "devicetype_run": devicetype_run,
        },
    )


@login_required
def devicetype_compare_netbox(request: HttpRequest, id: int) -> HttpResponseRedirect:
    if not request.user.is_superuser:  # type: ignore
        raise PermissionDenied

    try:
        requested_devicetype = DeviceType.objects.get(pk=id)
    except DeviceType.DoesNotExist:
        messages.error(request, "Device Type does not exist!")
        return redirect("frontend:devicetypes")

    if requested_devicetype.netbox_id == 0:
        messages.error(request, "Device Type is not linked to NetBox!")
        return redirect("frontend:devicetype_detail", id=id)

    try:
        TaskManager.add(tasks.NetboxCompareDeviceType(requested_devicetype.pk))
        messages.info(
            request,
            "Comparing data with Netbox - this can take some seconds...",
        )
    except Exception as exception:
        messages.error(request, exception)  # type: ignore

    return redirect("frontend:devicetype_detail", id=id)
