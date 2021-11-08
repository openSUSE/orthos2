import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.template.defaultfilters import urlize

from orthos2.frontend.templatetags.tags import vm_record
from orthos2.data.models import Annotation, Machine, RemotePower

from .decorators import check_permissions

logger = logging.getLogger('views')


@login_required
def annotation(request, machine_id):
    text = request.GET.get('text', None)

    annotation = Annotation.objects.create(
        machine_id=machine_id,
        reporter=request.user,
        text=text
    )

    data = {
        'text': urlize(annotation.text),
        'reporter': annotation.reporter.username,
        'date': '{:%Y-%m-%d}'.format(annotation.created)
    }
    return JsonResponse(data)


@login_required
@check_permissions(key='machine_id')
def powercycle(request, machine_id):
    """Power cycle machine and return result as JSON."""
    action = request.GET.get('action', None)

    try:
        machine = Machine.objects.get(pk=machine_id)
        result = machine.powercycle(action, user=request.user)

        if action == RemotePower.Action.STATUS:
            return JsonResponse({
                'type': 'status',
                'cls': 'info',
                'message':
                "Status: {}".format(result.capitalize())
            })

        if result:
            return JsonResponse({
                'type': 'status',
                'cls': 'success',
                'message': "Machine successfully power cycled!"
            })
        else:
            return JsonResponse({
                'type': 'status',
                'cls': 'danger',
                'message': "Power cycle failed!"
            })

    except Machine.DoesNotExist:
        return JsonResponse({
            'type': 'status',
            'cls': 'danger',
            'message': "Machine does not exist!"
        })
    except Exception as e:
        logger.exception(e)
        return JsonResponse({
            'type': 'status',
            'cls': 'danger',
            'message': str(e)
        })


@login_required
def virtualization_list(request, host_id):
    """Return VM list (libvirt)."""
    try:
        host = Machine.objects.get(pk=host_id)
        output = host.virtualization_api.get_list()

        return JsonResponse({
            'type': 'output',
            'output': output
        })
    except Exception as e:
        logger.exception(e)
        return JsonResponse({
            'type': 'status',
            'cls': 'danger',
            'message': str(e)
        })


@login_required
@check_permissions(key='host_id')
def virtualization_delete(request, host_id):
    """Delete a VM."""
    vm_id = request.GET.get('vm', None)

    if vm_id is None:
        raise Exception("No valid VM ID!")

    try:
        vm = Machine.objects.get(pk=vm_id)
        host = Machine.objects.get(pk=host_id)

        if host.virtualization_api is None:
            raise Exception("No virtualization API found!")

        if host.virtualization_api.remove(vm):
            vm.delete()

        vm_list = []

        for vm in host.get_virtual_machines():
            vm_list.append(vm_record(request, vm))

        return JsonResponse({
            'type': 'status',
            'cls': 'success',
            'message': "Virtual machine successfully deleted!",
            'vm_list': vm_list
        })
    except Exception as e:
        logger.exception(e)
        return JsonResponse({
            'type': 'status',
            'cls': 'danger',
            'message': str(e)
        })
