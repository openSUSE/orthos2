"""
All views that are under "/serverconfigs".
"""

from typing import Any, Dict

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from orthos2.data.models import ServerConfig
from orthos2.frontend.mixins import SuperuserRequiredMixin

FIELDS = ["key", "value"]


class ServerConfigListView(SuperuserRequiredMixin, ListView):
    model = ServerConfig
    template_name = "frontend/serverconfigs/serverconfigs.html"
    paginate_by = 50

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Server Configuration"
        return context


class NewServerConfig(SuperuserRequiredMixin, CreateView):
    model = ServerConfig
    template_name = "frontend/serverconfigs/new_serverconfig.html"
    success_url = reverse_lazy("frontend:serverconfigs")
    fields = FIELDS

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "New Server Configuration"
        context["action"] = "new"
        return context


class ServerConfigDetailedEdit(SuperuserRequiredMixin, UpdateView):
    model = ServerConfig
    template_name = "frontend/serverconfigs/new_serverconfig.html"
    success_url = reverse_lazy("frontend:serverconfigs")
    fields = FIELDS

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Server Configuration"
        context["action"] = "edit"
        return context


class DeleteServerConfig(SuperuserRequiredMixin, DeleteView):  # type: ignore
    model = ServerConfig
    template_name = "frontend/serverconfigs/serverconfig_confirm_deletion.html"
    success_url = reverse_lazy("frontend:serverconfigs")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Delete Server Configuration"
        return context


@login_required
def serverconfig_detail(request: HttpRequest, id: int) -> HttpResponse:
    if not request.user.is_superuser:  # type: ignore
        raise PermissionDenied

    try:
        serverconfig = ServerConfig.objects.get(pk=id)
    except ServerConfig.DoesNotExist:
        raise Http404("Server configuration does not exist")

    return render(
        request,
        "frontend/serverconfigs/detail/overview.html",
        {
            "serverconfig": serverconfig,
            "title": "Server Configuration {}".format(serverconfig.key),
        },
    )
