"""
All views that are under "/enclosure".
"""

from typing import TYPE_CHECKING, Any, Dict, List

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Q, QuerySet
from django.http import (
    Http404,
    HttpRequest,
    HttpResponse,
    HttpResponseBase,
    HttpResponseRedirect,
)
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from orthos2.data.models import Enclosure, Machine, Platform
from orthos2.taskmanager import tasks
from orthos2.taskmanager.models import TaskManager

if TYPE_CHECKING:
    from orthos2.types import AuthenticatedHttpRequest


class EnclosureListView(PermissionRequiredMixin, ListView):
    model = Enclosure
    template_name = "frontend/enclosures/enclosures.html"
    paginate_by = 50
    permission_required = "data.change_enclosure"

    @method_decorator(login_required)
    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        return super(EnclosureListView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet["Enclosure"]:
        """
        Return pre-filtered query set for every enclosure list.
        """
        filters: List[Q] = []

        if self.request.GET.get("query"):
            filters.append(Q(name__contains=self.request.GET.get("query")))

        if self.request.GET.get("platform"):
            filters.append(Q(platform__name=self.request.GET.get("platform")))

        enclosures = super().get_queryset().filter(*filters)  # type: ignore

        return enclosures

    def get_ordering(self) -> str:
        order_by = self.request.GET.get("order_by", None)
        order_direction = self.request.GET.get("order_direction", None)

        if order_by and order_direction in {"asc", "desc"}:
            ordering = (
                "{}".format(order_by)
                if order_direction == "desc"
                else "-{}".format(order_by)
            )
            return ordering
        return "name"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Enclosures"
        context["platforms"] = Platform.objects.all()
        context["enclosure_list"] = self.object_list  # type: ignore
        return context


class EnclosureDetailedEdit(PermissionRequiredMixin, UpdateView):
    model = Enclosure
    success_url = reverse_lazy("enclosures/<int:pk>")
    template_name = "frontend/enclosures/new_enclosure.html"
    success_url = reverse_lazy("frontend:enclosures")
    permission_required = "data.change_enclosure"

    fields = ["name", "platform", "netbox_id", "description"]

    @method_decorator(login_required)
    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        return super(EnclosureDetailedEdit, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Enclosure"
        context["action"] = "edit"
        return context


class NewEnclosure(PermissionRequiredMixin, CreateView):
    model = Enclosure
    template_name = "frontend/enclosures/new_enclosure.html"
    success_url = "/enclosures"
    permission_required = "data.change_enclosure"

    fields = ["name", "platform", "netbox_id", "description"]

    @method_decorator(login_required)
    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        return super(NewEnclosure, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "New Enclosure"
        context["action"] = "new"
        return context


class DeleteEnclosure(PermissionRequiredMixin, DeleteView):  # type: ignore
    model = Enclosure
    template_name = "frontend/enclosures/enclosure_confirm_deletion.html"
    success_url = reverse_lazy("frontend:enclosures")
    permission_required = "data.change_enclosure"

    @method_decorator(login_required)
    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        return super(DeleteEnclosure, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Delete Enclosure"
        return context


@login_required
@permission_required("data.change_enclosure")
def enclosure_machines(request: HttpRequest, id: int) -> HttpResponse:
    try:
        enclosure = Enclosure.objects.get(pk=id)
        machines = Machine.objects.filter(enclosure__id=id)
        return render(
            request,
            "frontend/enclosures/detail/machines.html",
            {
                "machines": machines,
                "enclosure": enclosure,
                "title": f"Enclosure {enclosure.name} Machines",
            },
        )
    except Enclosure.DoesNotExist:
        raise Http404("Enclosure does not exist")


@login_required
@permission_required("data.change_enclosure")
def enclosure_detail(request: HttpRequest, id: int) -> HttpResponse:
    try:
        enclosure = Enclosure.objects.get(pk=id)
        return render(
            request,
            "frontend/enclosures/detail/overview.html",
            {"enclosure": enclosure, "title": f"Enclosure {enclosure.name}"},
        )
    except Enclosure.DoesNotExist:
        raise Http404("Enclosure does not exist")


@login_required
def enclosure_fetch_netbox(request: HttpRequest, id: int) -> HttpResponseRedirect:
    try:
        requested_enclosure = Enclosure.objects.get(pk=id)
    except Machine.DoesNotExist:
        messages.error(request, "Enclosure does not exist!")
        return redirect("frontend:enclosures")

    try:
        TaskManager.add(tasks.NetboxFetchFullEnclosure(requested_enclosure.pk))
        messages.info(
            request,
            "Fetching data from Netbox for enclosure - this can take some seconds...",
        )
    except Exception as exception:
        messages.error(request, exception)  # type: ignore

    return redirect("frontend:enclosure_detail", id=id)


@login_required
def enclosure_netboxcomparison(
    request: "AuthenticatedHttpRequest", id: int
) -> HttpResponseBase:
    perm_list = [
        "data.view_enclosure",
    ]
    if not request.user.has_perms(perm_list):
        messages.error(request, "Not enough user permissions.")
        return redirect("enclosures")

    try:
        enclosure = Enclosure.objects.get(pk=id)
    except Enclosure.DoesNotExist:
        messages.error(request, "Enclosure does not exist.")
        return redirect("enclosures")

    if enclosure.netboxorthoscomparisionruns.count() > 0:
        enclosure_run = enclosure.netboxorthoscomparisionruns.latest(
            "compare_timestamp"
        )
    else:
        enclosure_run = None

    return render(
        request,
        "frontend/enclosures/detail/netbox_comparison.html",
        {
            "enclosure": enclosure,
            "title": "Netbox Comparison",
            "enclosure_run": enclosure_run,
        },
    )


@login_required
def enclosure_compare_netbox(request: HttpRequest, id: int) -> HttpResponseRedirect:
    try:
        requested_enclosure = Enclosure.objects.get(pk=id)
    except Enclosure.DoesNotExist:
        messages.error(request, "Enclosure does not exist!")
        return redirect("frontend:enclosures")

    try:
        TaskManager.add(tasks.NetboxCompareEnclosure(requested_enclosure.pk))
        messages.info(
            request,
            "Comparing data with Netbox - this can take some seconds...",
        )
    except Exception as exception:
        messages.error(request, exception)  # type: ignore

    return redirect("frontend:enclosure_detail", id=id)
