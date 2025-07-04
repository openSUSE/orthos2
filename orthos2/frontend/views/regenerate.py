"""
All views for "/regenerate".
"""

from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpRequest, JsonResponse

from orthos2.data.models import Machine
from orthos2.data.signals import (
    signal_cobbler_machine_update,
    signal_cobbler_regenerate,
    signal_serialconsole_regenerate,
)


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
