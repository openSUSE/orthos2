"""
All views that are under "/devicetypes".
"""

from typing import Any, Dict

from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseBase
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from orthos2.data.models import DeviceType
from orthos2.frontend.mixins import SuperuserRequiredMixin


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

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Device Types"
        return context


class NewDeviceType(SuperuserRequiredMixin, CreateView):
    model = DeviceType
    template_name = "frontend/devicetypes/new_devicetype.html"
    success_url = reverse_lazy("frontend:devicetypes")
    fields = ["name", "manufacturer", "is_cartridge", "description"]

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "New Device Type"
        context["action"] = "new"
        return context


class DeviceTypeDetailedEdit(SuperuserRequiredMixin, UpdateView):
    model = DeviceType
    template_name = "frontend/devicetypes/new_devicetype.html"
    success_url = reverse_lazy("frontend:devicetypes")
    fields = ["name", "manufacturer", "is_cartridge", "description"]

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
