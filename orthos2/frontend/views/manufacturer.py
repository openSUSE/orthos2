"""
All views that are under "/manufacturers".
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
from django.utils.decorators import method_decorator  # type: ignore
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from orthos2.data.models import DeviceType, Manufacturer
from orthos2.frontend.forms.manufacturer import ManufacturerForm
from orthos2.frontend.mixins import SuperuserRequiredMixin
from orthos2.taskmanager import tasks
from orthos2.taskmanager.models import TaskManager


class ManufacturerListView(ListView):  # type: ignore
    model = Manufacturer
    template_name = "frontend/manufacturers/manufacturers.html"
    paginate_by = 50

    # login is required, but any authenticated user may view the list
    @method_decorator(login_required)
    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet["Manufacturer"]:
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
        context["title"] = "Manufacturers"
        return context


class NewManufacturer(SuperuserRequiredMixin, CreateView):
    model = Manufacturer
    template_name = "frontend/manufacturers/new_manufacturer.html"
    success_url = reverse_lazy("frontend:manufacturers")
    form_class = ManufacturerForm

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "New Manufacturer"
        context["action"] = "new"
        return context


class ManufacturerDetailedEdit(SuperuserRequiredMixin, UpdateView):
    model = Manufacturer
    template_name = "frontend/manufacturers/new_manufacturer.html"
    success_url = reverse_lazy("frontend:manufacturers")
    form_class = ManufacturerForm

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Manufacturer"
        context["action"] = "edit"
        return context


class DeleteManufacturer(SuperuserRequiredMixin, DeleteView):  # type: ignore
    model = Manufacturer
    template_name = "frontend/manufacturers/manufacturer_confirm_deletion.html"
    success_url = reverse_lazy("frontend:manufacturers")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Delete Manufacturer"
        return context


@login_required
def manufacturer_detail(request: HttpRequest, id: int) -> HttpResponse:
    try:
        manufacturer = Manufacturer.objects.get(pk=id)
    except Manufacturer.DoesNotExist:
        raise Http404("Manufacturer does not exist")

    return render(
        request,
        "frontend/manufacturers/detail/overview.html",
        {
            "manufacturer": manufacturer,
            "title": "Manufacturer {}".format(manufacturer.name),
        },
    )


@login_required
def manufacturer_device_types(request: HttpRequest, id: int) -> HttpResponse:
    try:
        manufacturer = Manufacturer.objects.get(pk=id)
    except Manufacturer.DoesNotExist:
        raise Http404("Manufacturer does not exist")

    device_types = DeviceType.objects.filter(manufacturer__id=id)
    return render(
        request,
        "frontend/manufacturers/detail/devicetypes.html",
        {
            "manufacturer": manufacturer,
            "device_types": device_types,
            "title": f"Manufacturer {manufacturer.name} Device Types",
        },
    )


@login_required
def manufacturer_fetch_netbox(request: HttpRequest, id: int) -> HttpResponseRedirect:
    if not request.user.is_superuser:  # type: ignore
        raise PermissionDenied

    try:
        requested_manufacturer = Manufacturer.objects.get(pk=id)
    except Manufacturer.DoesNotExist:
        messages.error(request, "Manufacturer does not exist!")
        return redirect("frontend:manufacturers")

    if requested_manufacturer.netbox_id == 0:
        messages.error(request, "Manufacturer is not linked to NetBox!")
        return redirect("frontend:manufacturer_detail", id=id)

    try:
        TaskManager.add(tasks.NetboxFetchFullManufacturer(requested_manufacturer.pk))
        messages.info(
            request,
            "Fetching data from Netbox for manufacturer - this can take some seconds...",
        )
    except Exception as exception:
        messages.error(request, exception)  # type: ignore

    return redirect("frontend:manufacturer_detail", id=id)


@login_required
def manufacturer_netboxcomparison(request: HttpRequest, id: int) -> HttpResponse:
    try:
        manufacturer = Manufacturer.objects.get(pk=id)
    except Manufacturer.DoesNotExist:
        raise Http404("Manufacturer does not exist")

    if manufacturer.netboxorthoscomparisionruns.count() > 0:
        manufacturer_run = manufacturer.netboxorthoscomparisionruns.latest(
            "compare_timestamp"
        )
    else:
        manufacturer_run = None

    return render(
        request,
        "frontend/manufacturers/detail/netbox_comparison.html",
        {
            "manufacturer": manufacturer,
            "title": "Netbox Comparison",
            "manufacturer_run": manufacturer_run,
        },
    )


@login_required
def manufacturer_compare_netbox(request: HttpRequest, id: int) -> HttpResponseRedirect:
    if not request.user.is_superuser:  # type: ignore
        raise PermissionDenied

    try:
        requested_manufacturer = Manufacturer.objects.get(pk=id)
    except Manufacturer.DoesNotExist:
        messages.error(request, "Manufacturer does not exist!")
        return redirect("frontend:manufacturers")

    if requested_manufacturer.netbox_id == 0:
        messages.error(request, "Manufacturer is not linked to NetBox!")
        return redirect("frontend:manufacturer_detail", id=id)

    try:
        TaskManager.add(tasks.NetboxCompareManufacturer(requested_manufacturer.pk))
        messages.info(
            request,
            "Comparing data with Netbox - this can take some seconds...",
        )
    except Exception as exception:
        messages.error(request, exception)  # type: ignore

    return redirect("frontend:manufacturer_detail", id=id)
