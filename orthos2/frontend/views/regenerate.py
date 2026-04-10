"""
All views for "/regenerate".
"""

from typing import Any

from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render

from orthos2.data.models import Machine
from orthos2.data.signals import (
    signal_cobbler_machine_update,
    signal_cobbler_regenerate,
    signal_serialconsole_regenerate,
)
from orthos2.utils.cobbler import CobblerServer


def _collect_cobbler_diff(host: Machine) -> dict[str, Any]:
    target_domains = host.cobbler_server_for.all()
    orthos_fqdns: set[str] = set()
    cobbler_fqdns: set[str] = set()
    stale_fqdns: set[str] = set()

    for domain in target_domains:
        domain_orthos_fqdns = set(
            domain.machine_set.exclude(active=False).values_list("fqdn", flat=True)
        )
        orthos_fqdns.update(domain_orthos_fqdns)

        server = CobblerServer(domain)
        domain_cobbler_fqdns = server.get_machines()
        domain_suffix = "." + domain.name
        domain_scoped_fqdns = {
            fqdn for fqdn in domain_cobbler_fqdns if fqdn.endswith(domain_suffix)
        }

        cobbler_fqdns.update(domain_scoped_fqdns)
        stale_fqdns.update(domain_scoped_fqdns - domain_orthos_fqdns)

    return {
        "orthos": sorted(orthos_fqdns),
        "cobbler": sorted(cobbler_fqdns),
        "stale": sorted(stale_fqdns),
    }


@login_required
@permission_required("data.change_domain")
def regenerate_cobbler(request: HttpRequest) -> JsonResponse:
    """
    Serves the URL "/regenerate/cobbler".

    This regenerates all machine entries on all Cobbler servers.
    """
    signal_cobbler_regenerate.send(sender=None, domain_id=None)  # type: ignore
    return JsonResponse(
        {"type": "status", "cls": "success", "message": "Regeneration started"}
    )


@login_required
@permission_required("data.change_domain")
def regenerate_domain_cscreen(request: HttpRequest, host_id: int) -> JsonResponse:
    """
    Serves the URL "/regenerate/domain/cscreen/{host_id}".

    This regenerates the cscreen server for the whole domain.
    """
    try:
        machine = Machine.objects.get(pk=host_id)
    except ObjectDoesNotExist:
        return JsonResponse(
            {"type": "status", "cls": "danger", "message": "Machine does not exist"},
            status=404,
        )
    if not machine.is_cscreen_server():
        return JsonResponse(
            {
                "type": "status",
                "cls": "danger",
                "message": "Machine is not a cscreen server",
            },
            status=400,
        )
    signal_serialconsole_regenerate.send(  # type: ignore
        sender=None,
        cscreen_server_fqdn=machine.fqdn,
    )
    return JsonResponse(
        {"type": "status", "cls": "success", "message": "Regeneration started"}
    )


@login_required
@permission_required("data.change_domain")
def regenerate_domain_cobbler(request: HttpRequest, host_id: int) -> JsonResponse:
    """
    Serves the URL "/regenerate/domain/cobbler/{host_id}".

    This regenerates all domains that are managed by the given Cobbler server.
    """
    try:
        machine = Machine.objects.get(pk=host_id)
    except ObjectDoesNotExist:
        return JsonResponse(
            {"type": "status", "cls": "danger", "message": "Machine does not exist"},
            status=404,
        )
    if not machine.is_cobbler_server():
        return JsonResponse(
            {
                "type": "status",
                "cls": "danger",
                "message": "Machine is not a cobbler server",
            },
            status=400,
        )

    target_domains = machine.cobbler_server_for.all()
    # One Cobbler server might manage multiple domains
    for domain in target_domains:
        signal_cobbler_regenerate.send(sender=None, domain_id=domain.id)  # type: ignore
    return JsonResponse(
        {"type": "status", "cls": "success", "message": "Regeneration started"}
    )


@login_required
@permission_required("data.change_domain")
def cleanup_domain_cobbler(request: HttpRequest, host_id: int) -> JsonResponse:
    """
    Serves the URL "/cleanup/domain/cobbler/{host_id}".

    This allows diffing and pruning stale Cobbler machines without running regeneration.
    """
    try:
        machine = Machine.objects.get(pk=host_id)
    except ObjectDoesNotExist:
        return JsonResponse(
            {"type": "status", "cls": "danger", "message": "Machine does not exist"},
            status=404,
        )
    if not machine.is_cobbler_server():
        return JsonResponse(
            {
                "type": "status",
                "cls": "danger",
                "message": "Machine is not a cobbler server",
            },
            status=400,
        )

    mode = request.GET.get("mode")
    if mode == "diff":
        diff = _collect_cobbler_diff(machine)
        return JsonResponse(
            {
                "type": "status",
                "cls": "info",
                "message": "Cobbler diff collected",
                "orthos_machines": diff["orthos"],
                "cobbler_machines": diff["cobbler"],
                "stale_machines": diff["stale"],
                "delete_count": len(diff["stale"]),
            }
        )

    if mode == "prune":
        selected_fqdns = set(request.GET.getlist("fqdn"))
        diff = _collect_cobbler_diff(machine)
        allowed_fqdns = set(diff["stale"])
        deletable_fqdns = sorted(selected_fqdns & allowed_fqdns)

        target_domains = machine.cobbler_server_for.all()
        for domain in target_domains:
            domain_suffix = "." + domain.name
            server = CobblerServer(domain)
            for fqdn in deletable_fqdns:
                if fqdn.endswith(domain_suffix):
                    server.remove_by_name(fqdn)

        return JsonResponse(
            {
                "type": "status",
                "cls": "success",
                "message": "Deleted {count} machine(s) from Cobbler".format(
                    count=len(deletable_fqdns)
                ),
                "deleted_machines": deletable_fqdns,
                "delete_count": len(deletable_fqdns),
            }
        )

    if mode is None:
        mode = "diff"

    return JsonResponse(
        {
            "type": "status",
            "cls": "danger",
            "message": 'Unknown cleanup mode "{mode}"'.format(mode=mode),
        },
        status=400,
    )


@login_required
@permission_required("data.change_domain")
def cleanup_domain_cobbler_page(request: HttpRequest, host_id: int) -> HttpResponse:
    """
    Serves the URL "/cleanup/domain/cobbler/{host_id}/page".

    This renders the dedicated UI for reviewing and pruning stale Cobbler machines.
    """
    try:
        machine = Machine.objects.get(pk=host_id)
    except ObjectDoesNotExist:
        return JsonResponse(
            {"type": "status", "cls": "danger", "message": "Machine does not exist"},
            status=404,
        )

    if not machine.is_cobbler_server():
        return JsonResponse(
            {
                "type": "status",
                "cls": "danger",
                "message": "Machine is not a cobbler server",
            },
            status=400,
        )

    return render(
        request,
        "frontend/regenerate/cobbler_cleanup.html",
        {
            "machine": machine,
            "title": "Cobbler Cleanup",
        },
    )


@login_required
@permission_required("data.change_machine")
def regenerate_machine_motd(request: HttpRequest, host_id: int) -> JsonResponse:
    """
    Serves the URL "/regenerate/machine/motd/{host_id}".

    This regenerates the motd for the given machine.
    """
    try:
        machine = Machine.objects.get(pk=host_id)
    except ObjectDoesNotExist:
        return JsonResponse(
            {"type": "status", "cls": "danger", "message": "Machine does not exist"},
            status=404,
        )
    machine.update_motd(user=request.user)
    return JsonResponse(
        {"type": "status", "cls": "success", "message": "Update MOTD started"}
    )


@login_required
@permission_required("data.change_machine")
def regenerate_machine_cobbler(request: HttpRequest, host_id: int) -> JsonResponse:
    """
    Serves the URL "/regenerate/machine/cobbler/{host_id}".

    This regenerates the individual Cobbler configuration for the given machine.
    """
    try:
        machine = Machine.objects.get(pk=host_id)
    except ObjectDoesNotExist:
        return JsonResponse(
            {"type": "status", "cls": "danger", "message": "Machine does not exist"},
            status=404,
        )
    signal_cobbler_machine_update.send(  # type: ignore
        sender=None,
        domain_id=machine.fqdn_domain.id,
        machine_id=machine.id,
    )
    return JsonResponse(
        {"type": "status", "cls": "success", "message": "Regeneration started"}
    )
