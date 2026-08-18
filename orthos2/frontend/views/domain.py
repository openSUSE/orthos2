"""
All views that are under "/domains".
"""

from typing import Any, Dict

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from orthos2.data.models import Domain
from orthos2.frontend.mixins import SuperuserRequiredMixin

FIELDS = [
    "name",
    "cobbler_server",
    "cobbler_server_username",
    "cobbler_server_password",
    "tftp_server",
    "cscreen_server",
    "ip_v4",
    "ip_v6",
    "subnet_mask_v4",
    "subnet_mask_v6",
    "enable_v4",
    "enable_v6",
    "dynamic_range_v4_start",
    "dynamic_range_v4_end",
    "dynamic_range_v6_start",
    "dynamic_range_v6_end",
]


class DomainListView(SuperuserRequiredMixin, ListView):
    model = Domain
    template_name = "frontend/domains/domains.html"
    paginate_by = 50

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Domains"
        return context


class NewDomain(SuperuserRequiredMixin, CreateView):
    model = Domain
    template_name = "frontend/domains/new_domain.html"
    success_url = reverse_lazy("frontend:domains")
    fields = FIELDS

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "New Domain"
        context["action"] = "new"
        return context


class DomainDetailedEdit(SuperuserRequiredMixin, UpdateView):
    model = Domain
    template_name = "frontend/domains/new_domain.html"
    success_url = reverse_lazy("frontend:domains")
    fields = FIELDS

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Domain"
        context["action"] = "edit"
        return context


class DeleteDomain(SuperuserRequiredMixin, DeleteView):  # type: ignore
    model = Domain
    template_name = "frontend/domains/domain_confirm_deletion.html"
    success_url = reverse_lazy("frontend:domains")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Delete Domain"
        return context

    def form_valid(self, form: Any) -> HttpResponseRedirect:
        try:
            self.object.delete()
        except ValidationError as e:
            messages.error(self.request, e.message)
        return HttpResponseRedirect(self.get_success_url())


@login_required
def domain_detail(request: HttpRequest, id: int) -> HttpResponse:
    if not request.user.is_superuser:  # type: ignore
        raise PermissionDenied

    try:
        domain = Domain.objects.get(pk=id)
    except Domain.DoesNotExist:
        raise Http404("Domain does not exist")

    return render(
        request,
        "frontend/domains/detail/overview.html",
        {
            "domain": domain,
            "title": "Domain {}".format(domain.name),
        },
    )
