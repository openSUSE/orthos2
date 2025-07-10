import logging
from typing import TYPE_CHECKING, Any, Dict, List

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, JsonResponse
from django.template.defaultfilters import urlize

from orthos2.data.models import Annotation, Machine, RemotePower
from orthos2.frontend.decorators import check_permissions
from orthos2.frontend.templatetags.tags import vm_record

if TYPE_CHECKING:
    from orthos2.types import AuthenticatedHttpRequest

logger = logging.getLogger("views")


@login_required
def annotation(request: "AuthenticatedHttpRequest", machine_id: int) -> JsonResponse:
    text = request.GET.get("text", "")

    target_annotation = Annotation.objects.create(
        machine_id=machine_id,
        reporter=request.user,
        text=text,
    )

    data: Dict[str, Any] = {
        "text": urlize(target_annotation.text),
        "reporter": target_annotation.reporter.username  # type: ignore
        if target_annotation.reporter
        else "",
        "date": "{:%Y-%m-%d}".format(target_annotation.created),
    }
    return JsonResponse(data)


@login_required
@check_permissions(key="machine_id")
def powercycle(request: HttpRequest, machine_id: int) -> JsonResponse:
    """Power cycle machine and return result as JSON."""
    action = request.GET.get("action", None)

    try:
        machine = Machine.objects.get(pk=machine_id)
        result = machine.powercycle(action, user=request.user)

        if action == RemotePower.Action.STATUS:
            # This returns a str as a result. The type annotation is incorrect.
            return JsonResponse(
                {
                    "type": "status",
                    "cls": "info",
                    "message": "Status: {}".format(result.capitalize()),  # type: ignore
                }
            )

        if result:
            return JsonResponse(
                {
                    "type": "status",
                    "cls": "success",
                    "message": "Machine successfully power cycled!",
                }
            )
        else:
            return JsonResponse(
                {"type": "status", "cls": "danger", "message": "Power cycle failed!"}
            )

    except Machine.DoesNotExist:
        return JsonResponse(
            {"type": "status", "cls": "danger", "message": "Machine does not exist!"}
        )
    except Exception as e:
        logger.exception(e)
        return JsonResponse({"type": "status", "cls": "danger", "message": str(e)})


@login_required
def virtualization_list(request: HttpRequest, host_id: int) -> JsonResponse:
    """Return VM list (libvirt)."""
    try:
        host = Machine.objects.get(pk=host_id)
        output = host.virtualization_api.get_list()  # type: ignore

        return JsonResponse({"type": "output", "output": output})
    except Exception as e:
        logger.exception(e)
        return JsonResponse({"type": "status", "cls": "danger", "message": str(e)})


@login_required
@check_permissions(key="host_id")
def virtualization_delete(request: HttpRequest, host_id: int) -> JsonResponse:
    """Delete a VM."""
    vm_id = request.GET.get("vm", None)

    if vm_id is None:
        raise Exception("No valid VM ID!")

    try:
        vm = Machine.objects.get(pk=vm_id)
        host = Machine.objects.get(pk=host_id)

        if host.virtualization_api is None:
            raise Exception("No virtualization API found!")

        if host.virtualization_api.remove(vm):
            vm.delete()

        vm_list: List[str] = []

        vms = host.get_virtual_machines()
        if vms is not None:
            for vm in vms:
                vm_list.append(vm_record(request, vm))

        return JsonResponse(
            {
                "type": "status",
                "cls": "success",
                "message": "Virtual machine successfully deleted!",
                "vm_list": vm_list,
            }
        )
    except Exception as e:
        logger.exception(e)
        return JsonResponse({"type": "status", "cls": "danger", "message": str(e)})
