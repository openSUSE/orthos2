"""
All views that are under "/platforms".
"""

from typing import Any, Dict

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from orthos2.data.models import Platform
from orthos2.frontend.mixins import SuperuserRequiredMixin


class PlatformListView(SuperuserRequiredMixin, ListView):
    model = Platform
    template_name = "frontend/platforms/platforms.html"
    paginate_by = 50

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Platforms"
        return context


class NewPlatform(SuperuserRequiredMixin, CreateView):
    model = Platform
    template_name = "frontend/platforms/new_platform.html"
    success_url = reverse_lazy("frontend:platforms")
    fields = ["name", "manufacturer", "is_cartridge", "description"]

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "New Platform"
        context["action"] = "new"
        return context


class PlatformDetailedEdit(SuperuserRequiredMixin, UpdateView):
    model = Platform
    template_name = "frontend/platforms/new_platform.html"
    success_url = reverse_lazy("frontend:platforms")
    fields = ["name", "manufacturer", "is_cartridge", "description"]

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Platform"
        context["action"] = "edit"
        return context


class DeletePlatform(SuperuserRequiredMixin, DeleteView):
    model = Platform
    template_name = "frontend/platforms/platform_confirm_deletion.html"
    success_url = reverse_lazy("frontend:platforms")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Delete Platform"
        return context


@login_required
def platform_detail(request: HttpRequest, id: int) -> HttpResponse:
    if not request.user.is_superuser:  # type: ignore
        raise PermissionDenied

    try:
        platform = Platform.objects.get(pk=id)
    except Platform.DoesNotExist:
        raise Http404("Platform does not exist")

    return render(
        request,
        "frontend/platforms/detail/overview.html",
        {"platform": platform, "title": "Platform {}".format(platform.name)},
    )
