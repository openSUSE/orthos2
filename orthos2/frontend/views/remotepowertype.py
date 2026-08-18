"""
All views that are under "/remotepowertypes".
"""

from typing import Any, Dict

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from orthos2.data.models import RemotePowerType
from orthos2.frontend.mixins import SuperuserRequiredMixin

FIELDS = [
    "name",
    "device",
    "username",
    "password",
    "identity_file",
    "architectures",
    "systems",
    "use_port",
    "use_hostname_as_port",
]


class RemotePowerTypeListView(SuperuserRequiredMixin, ListView):
    model = RemotePowerType
    template_name = "frontend/remotepowertypes/remotepowertypes.html"
    paginate_by = 50

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Remote Power Types"
        return context


class NewRemotePowerType(SuperuserRequiredMixin, CreateView):
    model = RemotePowerType
    template_name = "frontend/remotepowertypes/new_remotepowertype.html"
    success_url = reverse_lazy("frontend:remotepowertypes")
    fields = FIELDS

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "New Remote Power Type"
        context["action"] = "new"
        return context


class RemotePowerTypeDetailedEdit(SuperuserRequiredMixin, UpdateView):
    model = RemotePowerType
    template_name = "frontend/remotepowertypes/new_remotepowertype.html"
    success_url = reverse_lazy("frontend:remotepowertypes")
    fields = FIELDS

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Remote Power Type"
        context["action"] = "edit"
        return context


class DeleteRemotePowerType(SuperuserRequiredMixin, DeleteView):  # type: ignore
    model = RemotePowerType
    template_name = "frontend/remotepowertypes/remotepowertype_confirm_deletion.html"
    success_url = reverse_lazy("frontend:remotepowertypes")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Delete Remote Power Type"
        return context


@login_required
def remotepowertype_detail(request: HttpRequest, id: int) -> HttpResponse:
    if not request.user.is_superuser:  # type: ignore
        raise PermissionDenied

    try:
        remotepowertype = RemotePowerType.objects.get(pk=id)
    except RemotePowerType.DoesNotExist:
        raise Http404("Remote power type does not exist")

    return render(
        request,
        "frontend/remotepowertypes/detail/overview.html",
        {
            "remotepowertype": remotepowertype,
            "title": "Remote Power Type {}".format(remotepowertype.name),
        },
    )
