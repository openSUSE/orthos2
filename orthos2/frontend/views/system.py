"""
All views that are under "/systems".
"""

from typing import Any, Dict

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from orthos2.data.models import System
from orthos2.frontend.mixins import SuperuserRequiredMixin


class SystemListView(SuperuserRequiredMixin, ListView):
    model = System
    template_name = "frontend/systems/systems.html"
    paginate_by = 50

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Systems"
        return context


class NewSystem(SuperuserRequiredMixin, CreateView):
    model = System
    template_name = "frontend/systems/new_system.html"
    success_url = reverse_lazy("frontend:systems")
    fields = ["name", "virtual", "allowBMC", "allowHypervisor", "administrative"]

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "New System"
        context["action"] = "new"
        return context


class SystemDetailedEdit(SuperuserRequiredMixin, UpdateView):
    model = System
    template_name = "frontend/systems/new_system.html"
    success_url = reverse_lazy("frontend:systems")
    fields = ["name", "virtual", "allowBMC", "allowHypervisor", "administrative"]

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit System"
        context["action"] = "edit"
        return context


class DeleteSystem(SuperuserRequiredMixin, DeleteView):  # type: ignore
    model = System
    template_name = "frontend/systems/system_confirm_deletion.html"
    success_url = reverse_lazy("frontend:systems")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Delete System"
        return context


@login_required
def system_detail(request: HttpRequest, id: int) -> HttpResponse:
    if not request.user.is_superuser:  # type: ignore
        raise PermissionDenied

    try:
        system = System.objects.get(pk=id)
    except System.DoesNotExist:
        raise Http404("System does not exist")

    return render(
        request,
        "frontend/systems/detail/overview.html",
        {"system": system, "title": "System {}".format(system.name)},
    )
