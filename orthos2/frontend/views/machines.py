"""
All views that are under "/machines".
"""

from typing import Any, Dict, List

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import AnonymousUser
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q, QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseBase
from django.shortcuts import redirect, render  # type: ignore
from django.utils.decorators import method_decorator  # type: ignore
from django.views.generic import ListView

from orthos2.data.models import Architecture, Domain, Machine, MachineGroup
from orthos2.frontend.forms.search import SearchForm


class MachineListView(ListView):  # type: ignore
    model = Machine
    template_name = "frontend/machines/list.html"
    paginate_by = 50

    # login is required for all machine lists
    @method_decorator(login_required)
    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        return super(MachineListView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Machine]:
        """
        Return pre-filtered query set for every machine list.

        Adminsitrative machines and administrative systems are excluded.
        """
        filters: List[Q] = []

        if self.request.GET.get("query"):
            filters.append(Q(fqdn__contains=self.request.GET.get("query")))

        if self.request.GET.get("arch"):
            filters.append(Q(architecture__name=self.request.GET.get("arch")))

        if self.request.GET.get("domain"):
            filters.append(Q(fqdn_domain__name=self.request.GET.get("domain")))

        if self.request.GET.get("machinegroup"):
            filters.append(Q(group__name=self.request.GET.get("machinegroup")))

        status = self.request.GET.get("status")
        if status and status == "ping":
            filters.append(
                Q(status_ipv4=Machine.StatusIP.REACHABLE)
                | Q(status_ipv4=Machine.StatusIP.CONFIRMED)
                | Q(status_ipv6=Machine.StatusIP.REACHABLE)
                | Q(status_ipv6=Machine.StatusIP.CONFIRMED)
            )
        elif status:
            filters.append(Q(**{"status_{}".format(status): True}))

        machines = Machine.view.get_queryset(user=self.request.user).filter(  # type: ignore
            *filters
        )

        return machines

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super(MachineListView, self).get_context_data(**kwargs)  # type: ignore
        context["machine_list"] = self.object_list  # type: ignore

        order_by = self.request.GET.get("order_by", None)
        order_direction = self.request.GET.get("order_direction", None)
        if order_by and order_direction in {"asc", "desc"}:
            context["machine_list"] = self.object_list.order_by(  # type: ignore
                "{}".format(order_by)
                if order_direction == "asc"
                else "-{}".format(order_by)
            )
            # hit the DB to check order_by fields and restore the queryset if something fails
            try:
                context["machine_list"] = list(context["machine_list"])  # type: ignore
            except KeyError:
                context["machine_list"] = self.object_list  # type: ignore

        paginator = Paginator(context["machine_list"], self.paginate_by)  # type: ignore

        page = self.request.GET.get("page", 1)

        try:
            machines = paginator.page(page)  # type: ignore
        except PageNotAnInteger:
            machines = paginator.page(1)  # type: ignore
        except EmptyPage:
            machines = paginator.page(paginator.num_pages)  # type: ignore

        context["architectures"] = Architecture.objects.all()
        context["domains"] = Domain.objects.all()
        context["machines"] = machines
        context["machinegroups"] = MachineGroup.objects.all()
        context["paginator"] = paginator
        return context


class AllMachineListView(MachineListView):
    """`All Machines` list view."""

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        return super(AllMachineListView, self).get(request, *args, **kwargs)

    def render_to_response(
        self,
        context: Dict[str, Any],
        **response_kwargs: Dict[str, Any],
    ) -> HttpResponse:
        context["title"] = "All Machines"
        return super(AllMachineListView, self).render_to_response(
            context, **response_kwargs
        )


class MyMachineListView(MachineListView):
    """`My Machines` list view."""

    def get_queryset(self) -> QuerySet["Machine"]:
        """Filter machines which are reserved by requesting user."""
        machines = super(MyMachineListView, self).get_queryset()
        return machines.filter(reserved_by=self.request.user)

    def render_to_response(
        self,
        context: Dict[str, Any],
        **response_kwargs: Dict[str, Any],
    ) -> HttpResponse:
        context["title"] = "My Machines"
        context["view"] = "my"
        return super(MyMachineListView, self).render_to_response(
            context, **response_kwargs
        )


class FreeMachineListView(MachineListView):
    """`Free Machines` list view."""

    def get_queryset(self) -> QuerySet["Machine"]:
        """Filter machines which are NOT reserved and NO dedicated VM hosts."""
        machines = super(FreeMachineListView, self).get_queryset()
        return machines.filter(
            reserved_by=None, vm_dedicated_host=False, administrative=False
        )

    def render_to_response(
        self,
        context: Dict[str, Any],
        **response_kwargs: Dict[str, Any],
    ) -> HttpResponse:
        context["title"] = "Free Machines"
        context["view"] = "free"
        return super(FreeMachineListView, self).render_to_response(
            context, **response_kwargs
        )


class VirtualMachineListView(MachineListView):
    """`Virtual Machines` list view."""

    def get_queryset(self) -> QuerySet["Machine"]:
        """Filter machines which are capable to run VMs and which are dedicated VM hosts."""
        machines = super(VirtualMachineListView, self).get_queryset()
        return machines.filter(vm_dedicated_host=True)

    def render_to_response(
        self, context: Dict[str, Any], **response_kwargs: Dict[str, Any]
    ) -> HttpResponse:
        """Add already running VMs."""
        context["title"] = "Virtual Machines"
        context["view"] = "virtual"

        vm_hosts = context["machines"]
        machines: List[Machine] = []

        # collect VMs of respective VM host
        for vm_host in vm_hosts:
            machines.append(vm_host)
            vm_machines = list(vm_host.get_virtual_machines())
            if vm_machines:
                machines.extend(vm_machines)

        context["machines"] = machines

        return super(VirtualMachineListView, self).render_to_response(
            context, **response_kwargs
        )


@login_required
def machine_search(request: HttpRequest) -> HttpResponse:
    if request.method == "GET":
        form = SearchForm()

    else:
        form = SearchForm(request.POST)

        if form.is_valid():
            if isinstance(request.user, AnonymousUser):
                messages.error(request, "You are not allowed to perform this action.")
                return redirect("frontend:login")
            machines = Machine.search.form(form.cleaned_data, request.user)  # type: ignore
            return render(
                request,
                "frontend/machines/list.html",
                {"machines": machines, "title": "Search Result"},
            )

    return render(
        request,
        "frontend/machines/search.html",
        {"form": form, "title": "Advanced Search"},
    )
