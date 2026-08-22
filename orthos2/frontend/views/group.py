"""
All views that are under "/groups".
"""

from typing import Any, Dict

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from orthos2.frontend.forms.group import GroupForm
from orthos2.frontend.mixins import SuperuserRequiredMixin


class GroupListView(SuperuserRequiredMixin, ListView):
    model = Group
    template_name = "frontend/groups/groups.html"
    paginate_by = 50
    ordering = "name"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Groups"
        return context


class NewGroup(SuperuserRequiredMixin, CreateView):
    model = Group
    template_name = "frontend/groups/new_group.html"
    success_url = reverse_lazy("frontend:groups")
    form_class = GroupForm

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "New Group"
        context["action"] = "new"
        return context


class GroupDetailedEdit(SuperuserRequiredMixin, UpdateView):
    model = Group
    template_name = "frontend/groups/new_group.html"
    success_url = reverse_lazy("frontend:groups")
    form_class = GroupForm

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Group"
        context["action"] = "edit"
        return context


class DeleteGroup(SuperuserRequiredMixin, DeleteView):  # type: ignore
    model = Group
    template_name = "frontend/groups/group_confirm_deletion.html"
    success_url = reverse_lazy("frontend:groups")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Delete Group"
        return context


@login_required
def group_detail(request: HttpRequest, id: int) -> HttpResponse:
    if not request.user.is_superuser:  # type: ignore
        raise PermissionDenied

    try:
        group = Group.objects.prefetch_related("permissions").get(pk=id)
    except Group.DoesNotExist:
        raise Http404("Group does not exist")

    return render(
        request,
        "frontend/groups/detail/overview.html",
        {"group": group, "title": "Group {}".format(group.name)},
    )
