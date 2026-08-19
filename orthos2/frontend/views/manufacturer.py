"""
All views that are under "/manufacturers".
"""

from typing import Any, Dict

from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseBase
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator  # type: ignore
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from orthos2.data.models import Manufacturer
from orthos2.frontend.mixins import SuperuserRequiredMixin


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
