"""
All views that are under "/domain/<domain_id>/architectures" and
"/domainarchitecture".

These manage `DomainAdmin` rows - the through-model of `Domain.supported_architectures`
that also carries the per-domain/architecture support contact email. The model is
named `DomainAdmin` in `orthos2.data.models.domain` (a historical name, unrelated to
Django Admin); this module and its routes are named "domainarchitecture" to avoid
that confusion.
"""

from typing import Any, Dict

from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from orthos2.data.models import Domain, DomainAdmin
from orthos2.frontend.mixins import SuperuserRequiredMixin

FIELDS = ["arch", "contact_email"]


class DomainArchitectureListView(SuperuserRequiredMixin, ListView):
    model = DomainAdmin
    template_name = "frontend/domainarchitectures/domainarchitectures.html"

    def get_queryset(self):  # type: ignore
        self.domain = get_object_or_404(Domain, pk=self.kwargs["domain_id"])
        return DomainAdmin.objects.filter(domain=self.domain)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["domain"] = self.domain
        context["title"] = "Supported Architectures for {}".format(self.domain.name)
        return context


class NewDomainArchitecture(SuperuserRequiredMixin, CreateView):
    model = DomainAdmin
    template_name = "frontend/domainarchitectures/new_domainarchitecture.html"
    fields = FIELDS

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Any:
        self.domain = get_object_or_404(Domain, pk=self.kwargs["domain_id"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form: Any) -> Any:
        form.instance.domain = self.domain
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse_lazy(
            "frontend:domain_architectures", kwargs={"domain_id": self.domain.pk}
        )

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["domain"] = self.domain
        context["title"] = "New Supported Architecture for {}".format(self.domain.name)
        context["action"] = "new"
        return context


class DomainArchitectureDetailedEdit(SuperuserRequiredMixin, UpdateView):
    model = DomainAdmin
    template_name = "frontend/domainarchitectures/new_domainarchitecture.html"
    fields = FIELDS

    def get_success_url(self) -> str:
        return reverse_lazy(
            "frontend:domain_architectures",
            kwargs={"domain_id": self.object.domain_id},
        )

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["domain"] = self.object.domain
        context["title"] = "Edit Supported Architecture for {}".format(
            self.object.domain.name
        )
        context["action"] = "edit"
        return context


class DeleteDomainArchitecture(SuperuserRequiredMixin, DeleteView):  # type: ignore
    model = DomainAdmin
    template_name = (
        "frontend/domainarchitectures/domainarchitecture_confirm_deletion.html"
    )

    def get_success_url(self) -> str:
        return reverse_lazy(
            "frontend:domain_architectures",
            kwargs={"domain_id": self.object.domain_id},
        )

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Delete Supported Architecture"
        return context
