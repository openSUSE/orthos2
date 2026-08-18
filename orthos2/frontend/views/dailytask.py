"""
All views that are under "/dailytasks".
"""

from datetime import timedelta
from typing import Any, Dict

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render  # type: ignore
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from orthos2.frontend.mixins import SuperuserRequiredMixin
from orthos2.taskmanager.models import DailyTask


class DailyTaskListView(SuperuserRequiredMixin, ListView):
    model = DailyTask
    template_name = "frontend/dailytasks/dailytasks.html"
    paginate_by = 50

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Daily Tasks"
        return context


class NewDailyTask(SuperuserRequiredMixin, CreateView):
    model = DailyTask
    template_name = "frontend/dailytasks/new_dailytask.html"
    success_url = reverse_lazy("frontend:dailytasks")
    fields = ["name", "module", "arguments", "priority", "enabled"]

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "New Daily Task"
        context["action"] = "new"
        return context


class DailyTaskDetailedEdit(SuperuserRequiredMixin, UpdateView):
    model = DailyTask
    template_name = "frontend/dailytasks/new_dailytask.html"
    success_url = reverse_lazy("frontend:dailytasks")
    fields = ["name", "module", "arguments", "priority", "enabled"]

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Daily Task"
        context["action"] = "edit"
        return context


class DeleteDailyTask(SuperuserRequiredMixin, DeleteView):  # type: ignore
    model = DailyTask
    template_name = "frontend/dailytasks/dailytask_confirm_deletion.html"
    success_url = reverse_lazy("frontend:dailytasks")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Delete Daily Task"
        return context


@login_required
def dailytask_detail(request: HttpRequest, id: int) -> HttpResponse:
    if not request.user.is_superuser:  # type: ignore
        raise PermissionDenied

    try:
        dailytask = DailyTask.objects.get(pk=id)
    except DailyTask.DoesNotExist:
        raise Http404("Daily task does not exist")

    return render(
        request,
        "frontend/dailytasks/detail/overview.html",
        {"dailytask": dailytask, "title": "Daily Task {}".format(dailytask.name)},
    )


@require_POST
@login_required
def dailytask_execute(request: HttpRequest, id: int) -> HttpResponseRedirect:
    """Force a daily task to execute on the taskmanager's next poll."""
    if not request.user.is_superuser:  # type: ignore
        raise PermissionDenied

    task = get_object_or_404(DailyTask, pk=id)

    if not task.enabled:
        messages.warning(request, "Daily task '{}' is disabled.".format(task.name))
    elif task.running:
        messages.warning(request, "Task is already running!")
    else:
        task.executed_at = timezone.now() - timedelta(days=1)
        task.save()
        messages.info(request, "Executing daily task '{}'...".format(task.name))

    return redirect("frontend:dailytask_detail", id=task.pk)


@require_POST
@login_required
def dailytask_switch(request: HttpRequest, id: int) -> HttpResponseRedirect:
    """Enable or disable a daily task."""
    if not request.user.is_superuser:  # type: ignore
        raise PermissionDenied

    task = get_object_or_404(DailyTask, pk=id)
    action = request.POST.get("action")

    if action == "enable":
        task.enabled = True
        # Prevent the task from starting to run immediately.
        task.executed_at = timezone.now()
    elif action == "disable":
        task.enabled = False
        task.running = False
    else:
        raise Http404("Unknown action")

    task.save()
    messages.info(request, "Successfully {}d task '{}'.".format(action, task.name))

    return redirect("frontend:dailytask_detail", id=task.pk)
