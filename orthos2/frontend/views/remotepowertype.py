"""
All views that are under "/remotepowertypes".
"""

from typing import Any, Dict, List

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Case, Count, IntegerField, QuerySet, Value, When
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from orthos2.data.models import BMC, RemotePower, RemotePowerDevice, RemotePowerType
from orthos2.frontend.mixins import SuperuserRequiredMixin

FIELDS = [
    "name",
    "device",
    "username",
    "password",
    "identity_file",
    "architectures",
    "systems",
    "use_port",
    "use_hostname_as_port",
]


class RemotePowerTypeListView(SuperuserRequiredMixin, ListView):
    model = RemotePowerType
    template_name = "frontend/remotepowertypes/remotepowertypes.html"
    paginate_by = 50

    def get_queryset(self) -> QuerySet["RemotePowerType"]:
        # RemotePowerType is used by three reverse relations (RemotePowerDevice,
        # BMC, RemotePower) depending on `device`, but they aren't independent:
        # RemotePower.save() mirrors remote_power_device.fence_agent (for
        # "rpowerdevice") or machine.bmc.fence_agent (for "bmc") onto its own
        # fence_agent field, so summing all three would double-count any machine
        # that has both a RemotePowerDevice/BMC and an explicit RemotePower row.
        # Only "hypervisor" has no other model backing it, so RemotePower.fence_agent
        # is the ground truth there. Pick the one relevant count per row instead.
        queryset = (
            super()
            .get_queryset()  # type: ignore[attr-defined]
            .annotate(
                rpowerdevice_count=Count("remotepowerdevice", distinct=True),
                bmc_count=Count("bmc", distinct=True),
                remotepower_count=Count("remotepower", distinct=True),
            )
            .annotate(
                device_count=Case(
                    When(device="rpowerdevice", then="rpowerdevice_count"),
                    When(device="bmc", then="bmc_count"),
                    When(device="hypervisor", then="remotepower_count"),
                    default=Value(0),
                    output_field=IntegerField(),
                )
            )
        )

        device_filter = self.request.GET.get("device")
        if device_filter in ("bmc", "rpowerdevice", "hypervisor"):
            queryset = queryset.filter(device=device_filter)

        return queryset

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Remote Power Types"
        return context


class NewRemotePowerType(SuperuserRequiredMixin, CreateView):
    model = RemotePowerType
    template_name = "frontend/remotepowertypes/new_remotepowertype.html"
    success_url = reverse_lazy("frontend:remotepowertypes")
    fields = FIELDS

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "New Remote Power Type"
        context["action"] = "new"
        return context


class RemotePowerTypeDetailedEdit(SuperuserRequiredMixin, UpdateView):
    model = RemotePowerType
    template_name = "frontend/remotepowertypes/new_remotepowertype.html"
    success_url = reverse_lazy("frontend:remotepowertypes")
    fields = FIELDS

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Remote Power Type"
        context["action"] = "edit"
        return context


class DeleteRemotePowerType(SuperuserRequiredMixin, DeleteView):  # type: ignore
    model = RemotePowerType
    template_name = "frontend/remotepowertypes/remotepowertype_confirm_deletion.html"
    success_url = reverse_lazy("frontend:remotepowertypes")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Delete Remote Power Type"
        return context


@login_required
def remotepowertype_detail(request: HttpRequest, id: int) -> HttpResponse:
    if not request.user.is_superuser:  # type: ignore
        raise PermissionDenied

    try:
        remotepowertype = RemotePowerType.objects.get(pk=id)
    except RemotePowerType.DoesNotExist:
        raise Http404("Remote power type does not exist")

    return render(
        request,
        "frontend/remotepowertypes/detail/overview.html",
        {
            "remotepowertype": remotepowertype,
            "title": "Remote Power Type {}".format(remotepowertype.name),
        },
    )


@login_required
def remotepowertype_devices(request: HttpRequest, id: int) -> HttpResponse:
    if not request.user.is_superuser:  # type: ignore
        raise PermissionDenied

    try:
        remotepowertype = RemotePowerType.objects.get(pk=id)
    except RemotePowerType.DoesNotExist:
        raise Http404("Remote power type does not exist")

    # Which reverse relation holds the "devices" using this fence agent depends
    # on its category - only one of RemotePowerDevice/BMC/RemotePower ever
    # applies (mirrors RemotePowerTypeListView.get_queryset()'s device_count).
    devices: List[Dict[str, Any]] = []
    if remotepowertype.device == "bmc":
        for bmc in (
            BMC.objects.filter(fence_agent=remotepowertype)
            .select_related("machine")
            .order_by("machine__fqdn")
        ):
            devices.append(
                {
                    "label": bmc.machine.fqdn,
                    "url": reverse("frontend:detail", args=[bmc.machine.pk]),
                    "netbox_id": bmc.machine.netbox_id,
                }
            )
    elif remotepowertype.device == "hypervisor":
        for remotepower in (
            RemotePower.objects.filter(fence_agent=remotepowertype)
            .select_related("machine")
            .order_by("machine__fqdn")
        ):
            devices.append(
                {
                    "label": remotepower.machine.fqdn,
                    "url": reverse("frontend:detail", args=[remotepower.machine.pk]),
                    "netbox_id": remotepower.machine.netbox_id,
                }
            )
    else:
        for remotepowerdevice in RemotePowerDevice.objects.filter(
            fence_agent=remotepowertype
        ).order_by("fqdn"):
            devices.append(
                {
                    "label": remotepowerdevice.fqdn,
                    "url": reverse(
                        "frontend:remotepowerdevice_detail", args=[remotepowerdevice.pk]
                    ),
                    "netbox_id": remotepowerdevice.netbox_id,
                }
            )

    return render(
        request,
        "frontend/remotepowertypes/detail/devices.html",
        {
            "remotepowertype": remotepowertype,
            "devices": devices,
            "title": "Remote Power Type {}".format(remotepowertype.name),
        },
    )
