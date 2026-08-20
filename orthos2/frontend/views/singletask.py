"""
All views that are under "/singletasks".
"""

from typing import Any, Dict

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from orthos2.frontend.forms.task import SingleTaskForm
from orthos2.frontend.mixins import SuperuserRequiredMixin
from orthos2.taskmanager.models import SingleTask


class SingleTaskListView(SuperuserRequiredMixin, ListView):
    model = SingleTask
    template_name = "frontend/singletasks/singletasks.html"
    paginate_by = 50

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Single Tasks"
        return context


class NewSingleTask(SuperuserRequiredMixin, CreateView):
    model = SingleTask
    template_name = "frontend/singletasks/new_singletask.html"
    success_url = reverse_lazy("frontend:singletasks")
    form_class = SingleTaskForm

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "New Single Task"
        context["action"] = "new"
        return context


class SingleTaskDetailedEdit(SuperuserRequiredMixin, UpdateView):
    model = SingleTask
    template_name = "frontend/singletasks/new_singletask.html"
    success_url = reverse_lazy("frontend:singletasks")
    form_class = SingleTaskForm

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Single Task"
        context["action"] = "edit"
        return context


class DeleteSingleTask(SuperuserRequiredMixin, DeleteView):  # type: ignore
    model = SingleTask
    template_name = "frontend/singletasks/singletask_confirm_deletion.html"
    success_url = reverse_lazy("frontend:singletasks")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Delete Single Task"
        return context


@login_required
def singletask_detail(request: HttpRequest, id: int) -> HttpResponse:
    if not request.user.is_superuser:  # type: ignore
        raise PermissionDenied

    try:
        singletask = SingleTask.objects.get(pk=id)
    except SingleTask.DoesNotExist:
        raise Http404("Single task does not exist")

    return render(
        request,
        "frontend/singletasks/detail/overview.html",
        {"singletask": singletask, "title": "Single Task {}".format(singletask.name)},
    )
