"""
All views that are under "/serialconsoletypes".
"""

from typing import Any, Dict

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from orthos2.data.models import SerialConsoleType
from orthos2.frontend.mixins import SuperuserRequiredMixin


class SerialConsoleTypeListView(SuperuserRequiredMixin, ListView):
    model = SerialConsoleType
    template_name = "frontend/serialconsoletypes/serialconsoletypes.html"
    paginate_by = 50

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Serial Console Types"
        return context


class NewSerialConsoleType(SuperuserRequiredMixin, CreateView):
    model = SerialConsoleType
    template_name = "frontend/serialconsoletypes/new_serialconsoletype.html"
    success_url = reverse_lazy("frontend:serialconsoletypes")
    fields = ["name", "command", "comment", "has_ipmi_sol"]

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "New Serial Console Type"
        context["action"] = "new"
        return context


class SerialConsoleTypeDetailedEdit(SuperuserRequiredMixin, UpdateView):
    model = SerialConsoleType
    template_name = "frontend/serialconsoletypes/new_serialconsoletype.html"
    success_url = reverse_lazy("frontend:serialconsoletypes")
    fields = ["name", "command", "comment", "has_ipmi_sol"]

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Serial Console Type"
        context["action"] = "edit"
        return context


class DeleteSerialConsoleType(SuperuserRequiredMixin, DeleteView):  # type: ignore
    model = SerialConsoleType
    template_name = (
        "frontend/serialconsoletypes/serialconsoletype_confirm_deletion.html"
    )
    success_url = reverse_lazy("frontend:serialconsoletypes")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Delete Serial Console Type"
        return context


@login_required
def serialconsoletype_detail(request: HttpRequest, id: int) -> HttpResponse:
    if not request.user.is_superuser:  # type: ignore
        raise PermissionDenied

    try:
        serialconsoletype = SerialConsoleType.objects.get(pk=id)
    except SerialConsoleType.DoesNotExist:
        raise Http404("Serial console type does not exist")

    return render(
        request,
        "frontend/serialconsoletypes/detail/overview.html",
        {
            "serialconsoletype": serialconsoletype,
            "title": "Serial Console Type {}".format(serialconsoletype.name),
        },
    )
