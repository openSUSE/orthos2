"""
All views that are under "/manufacturers".
"""

from typing import Any, Dict

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from orthos2.data.models import Manufacturer
from orthos2.frontend.mixins import SuperuserRequiredMixin


class ManufacturerListView(SuperuserRequiredMixin, ListView):
    model = Manufacturer
    template_name = "frontend/manufacturers/manufacturers.html"
    paginate_by = 50

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Manufacturers"
        return context


class NewManufacturer(SuperuserRequiredMixin, CreateView):
    model = Manufacturer
    template_name = "frontend/manufacturers/new_manufacturer.html"
    success_url = reverse_lazy("frontend:manufacturers")
    fields = ["name"]

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "New Manufacturer"
        context["action"] = "new"
        return context


class ManufacturerDetailedEdit(SuperuserRequiredMixin, UpdateView):
    model = Manufacturer
    template_name = "frontend/manufacturers/new_manufacturer.html"
    success_url = reverse_lazy("frontend:manufacturers")
    fields = ["name"]

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
    if not request.user.is_superuser:  # type: ignore
        raise PermissionDenied

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
