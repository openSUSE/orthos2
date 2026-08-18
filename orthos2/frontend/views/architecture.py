"""
All views that are under "/architectures".
"""

from typing import Any, Dict

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from orthos2.data.models import Architecture
from orthos2.frontend.mixins import SuperuserRequiredMixin

FIELDS = ["name", "dhcp_filename", "contact_email", "default_profile"]


class ArchitectureListView(SuperuserRequiredMixin, ListView):
    model = Architecture
    template_name = "frontend/architectures/architectures.html"
    paginate_by = 50

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Architectures"
        return context


class NewArchitecture(SuperuserRequiredMixin, CreateView):
    model = Architecture
    template_name = "frontend/architectures/new_architecture.html"
    success_url = reverse_lazy("frontend:architectures")
    fields = FIELDS

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "New Architecture"
        context["action"] = "new"
        return context


class ArchitectureDetailedEdit(SuperuserRequiredMixin, UpdateView):
    model = Architecture
    template_name = "frontend/architectures/new_architecture.html"
    success_url = reverse_lazy("frontend:architectures")
    fields = FIELDS

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Architecture"
        context["action"] = "edit"
        return context


class DeleteArchitecture(SuperuserRequiredMixin, DeleteView):  # type: ignore
    model = Architecture
    template_name = "frontend/architectures/architecture_confirm_deletion.html"
    success_url = reverse_lazy("frontend:architectures")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Delete Architecture"
        return context

    def form_valid(self, form: Any) -> HttpResponseRedirect:
        try:
            self.object.delete()
        except ValidationError as e:
            messages.error(self.request, e.message)
        return HttpResponseRedirect(self.get_success_url())


@login_required
def architecture_detail(request: HttpRequest, id: int) -> HttpResponse:
    if not request.user.is_superuser:  # type: ignore
        raise PermissionDenied

    try:
        architecture = Architecture.objects.get(pk=id)
    except Architecture.DoesNotExist:
        raise Http404("Architecture does not exist")

    return render(
        request,
        "frontend/architectures/detail/overview.html",
        {
            "architecture": architecture,
            "title": "Architecture {}".format(architecture.name),
        },
    )
