from django.conf.urls import re_path
from django.http import HttpResponseRedirect, JsonResponse

from api.commands import BaseAPIView, get_machine
from api.serializers.machine import MachineSerializer
from api.serializers.misc import ErrorMessage, Serializer
from data.models import Machine


class InfoCommand(BaseAPIView):

    METHOD = 'GET'
    URL = '/machine'
    ARGUMENTS = (
        ['fqdn'],
    )

    HELP_SHORT = "Retrieve information about a machine."
    HELP = """Command to get information about a machine.

Usage:
    INFO <fqdn>

Arguments:
    fqdn - FQDN or hostname of the machine.

Example:
    INFO foo.domain.tld
    """

    @staticmethod
    def get_urls():
        return [
            re_path(r'^machine$', InfoCommand.as_view(), name='machine'),
        ]

    @staticmethod
    def get_tabcompletion():
        return list(Machine.api.all().values_list('fqdn', flat=True))

    def get(self, request, *args, **kwargs):
        """Return machine information."""
        fqdn = request.GET.get('fqdn', None)
        response = {}

        try:
            result = get_machine(
                fqdn,
                redirect_to='api:machine',
                data=request.GET
            )
            if isinstance(result, Serializer):
                return result.as_json
            elif isinstance(result, HttpResponseRedirect):
                return result
            machine = result
        except Exception as e:
            return ErrorMessage(str(e)).as_json

        machine.enclosure.fetch_location(machine.pk)
        machine = MachineSerializer(machine)

        order = [
            'fqdn',
            'architecture',
            'ipv4',
            'ipv6',
            'serial_number',
            'product_code',
            'comment',
            'nda',
            None,
            'system',
            'enclosure',
            'group',
            None,
            'location_room',
            'location_rack',
            'location_rack_position',
            None,
            'reserved_by',
            'reserved_reason',
            'reserved_at',
            'reserved_until',
            None,
            'status_ipv4',
            'status_ipv6',
            'status_ssh',
            'status_login',
            'status_abuild',
            None,
            'cpu_model',
            'cpu_id',
            'cpu_physical',
            'cpu_cores',
            'cpu_threads',
            'cpu_flags',
            'ram_amount',
            None,
            'serial_type',
            'serial_cscreen_server',
            'serial_management_bmc',
            'serial_console_server',
            'serial_device',
            'serial_port',
            'serial_command',
            'serial_comment',
            'serial_baud_rate',
            'serial_kernel_device',
            None,
            'power_type',
            'power_management_bmc',
            'power_host',
            'power_port',
            'power_device',
            'power_comment',
            [
                'installations', [
                    'distribution',
                    'active',
                    'partition',
                    'architecture',
                    'kernelversion'
                ]
            ],
            [
                'networkinterfaces', [
                    'mac_address',
                    'name',
                    'ethernet_type',
                    'driver_module',
                    'primary',
                ]
            ],
            [
                'annotations', [
                    'text',
                    'reporter',
                    'created'
                ]
            ]
        ]

        response['header'] = {'type': 'INFO', 'order': order}
        response['data'] = machine.data_info

        return JsonResponse(response)
