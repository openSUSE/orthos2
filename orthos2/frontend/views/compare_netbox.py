"""
This view module contains all views that display the NetboxOrthosComparisionRun model and its detailed results.
"""

import uuid
from typing import TYPE_CHECKING, Any, Dict, List

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q, QuerySet
from django.http import HttpRequest, HttpResponseBase
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator  # type: ignore
from django.views.generic import ListView

from orthos2.data.models.netboxorthoscomparision import NetboxOrthosComparisionRun

if TYPE_CHECKING:
    from orthos2.types import AuthenticatedHttpRequest


class NetboxOrthosComparisionRunListView(PermissionRequiredMixin, ListView):
    model = NetboxOrthosComparisionRun
    template_name = "frontend/netboxorthoscomparison/overview.html"
    permission_required = "data.change_netboxorthoscomparisonrun"
    paginate_by = 50

    # login is required for all machine lists
    @method_decorator(login_required)
    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        return super(NetboxOrthosComparisionRunListView, self).dispatch(
            request, *args, **kwargs
        )

    def get_queryset(self) -> "QuerySet[NetboxOrthosComparisionRun]":
        filters: List[Q] = []

        object_type = self.request.GET.get("object_type")
        if object_type:
            filters.append(Q(object_type=object_type))

        date_from = self.request.GET.get("date_from")
        if date_from:
            filters.append(Q(compare_timestamp__date__gte=date_from))

        date_to = self.request.GET.get("date_to")
        if date_to:
            filters.append(Q(compare_timestamp__date__lte=date_to))

        query = self.request.GET.get("query")
        if query:
            filters.append(
                Q(object_bmc__fqdn__icontains=query)
                | Q(object_device_type__name__icontains=query)
                | Q(object_enclosure__name__icontains=query)
                | Q(object_machine__fqdn__icontains=query)
                | Q(object_manufacturer__name__icontains=query)
                | Q(object_network_interface__name__icontains=query)
                | Q(object_remote_power_device__fqdn__icontains=query)
            )

        return super().get_queryset().filter(*filters)  # type: ignore

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super(NetboxOrthosComparisionRunListView, self).get_context_data(**kwargs)  # type: ignore
        context["run_list"] = self.object_list  # type: ignore

        context[
            "object_types"
        ] = NetboxOrthosComparisionRun.NetboxOrthosComparisionItemTypes.choices
        context["object_type"] = self.request.GET.get("object_type", "")
        context["date_from"] = self.request.GET.get("date_from", "")
        context["date_to"] = self.request.GET.get("date_to", "")

        order_by = self.request.GET.get("order_by", None)
        order_direction = self.request.GET.get("order_direction", None)
        if order_by and order_direction in {"asc", "desc"}:
            context["run_list"] = self.object_list.order_by(  # type: ignore
                "{}".format(order_by)
                if order_direction == "asc"
                else "-{}".format(order_by)
            )
            # hit the DB to check order_by fields and restore the queryset if something fails
            try:
                context["run_list"] = list(context["run_list"])  # type: ignore
            except KeyError:
                context["run_list"] = self.object_list  # type: ignore

        paginator = Paginator(context["run_list"], self.paginate_by)  # type: ignore

        page = self.request.GET.get("page", 1)

        try:
            comparison_runs = paginator.page(page)  # type: ignore
        except PageNotAnInteger:
            comparison_runs = paginator.page(1)  # type: ignore
        except EmptyPage:
            comparison_runs = paginator.page(paginator.num_pages)  # type: ignore

        context["title"] = "NetBox Comparison Runs"
        context["runs"] = comparison_runs
        return context


@login_required
@permission_required("data.change_netboxorthoscomparisonrun")
def netboxorthoscomparisonrun(
    request: "AuthenticatedHttpRequest", id: str
) -> HttpResponseBase:
    try:
        uuid.UUID(id)
    except ValueError:
        messages.error(request, "NetboxOrthosComparisonRun does not exist.")
        return redirect("frontend:compare_netbox_overview")
    try:
        requested_run = NetboxOrthosComparisionRun.objects.get(pk=id)
    except NetboxOrthosComparisionRun.DoesNotExist:
        messages.error(request, "NetboxOrthosComparisonRun does not exist.")
        return redirect("frontend:compare_netbox_overview")

    return render(
        request,
        "frontend/netboxorthoscomparison/details.html",
        {
            "run": requested_run,
            "title": "NetBox Comparison Run",
        },
    )
