"""
All views that are under "/vendors".
"""

from typing import Any, Dict

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from orthos2.data.models import Vendor
from orthos2.frontend.mixins import SuperuserRequiredMixin


class VendorListView(SuperuserRequiredMixin, ListView):
    model = Vendor
    template_name = "frontend/vendors/vendors.html"
    paginate_by = 50

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Vendors"
        return context


class NewVendor(SuperuserRequiredMixin, CreateView):
    model = Vendor
    template_name = "frontend/vendors/new_vendor.html"
    success_url = reverse_lazy("frontend:vendors")
    fields = ["name"]

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "New Vendor"
        context["action"] = "new"
        return context


class VendorDetailedEdit(SuperuserRequiredMixin, UpdateView):
    model = Vendor
    template_name = "frontend/vendors/new_vendor.html"
    success_url = reverse_lazy("frontend:vendors")
    fields = ["name"]

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Vendor"
        context["action"] = "edit"
        return context


class DeleteVendor(SuperuserRequiredMixin, DeleteView):
    model = Vendor
    template_name = "frontend/vendors/vendor_confirm_deletion.html"
    success_url = reverse_lazy("frontend:vendors")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Delete Vendor"
        return context


@login_required
def vendor_detail(request: HttpRequest, id: int) -> HttpResponse:
    if not request.user.is_superuser:  # type: ignore
        raise PermissionDenied

    try:
        vendor = Vendor.objects.get(pk=id)
    except Vendor.DoesNotExist:
        raise Http404("Vendor does not exist")

    return render(
        request,
        "frontend/vendors/detail/overview.html",
        {"vendor": vendor, "title": "Vendor {}".format(vendor.name)},
    )
