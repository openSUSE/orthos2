from orthos2.api.commands import BaseAPIView, get_machine
from orthos2.api.serializers.misc import ErrorMessage, InfoMessage, Message, Serializer
from django.conf.urls import re_path
from django.http import HttpResponseRedirect
from orthos2.taskmanager.tasks.machinetasks import MachineCheck
from orthos2.taskmanager.tasks.ansible import Ansible
from orthos2.taskmanager import tasks
from orthos2.taskmanager.models import TaskManager


class RescanCommand(BaseAPIView):

    METHOD = 'GET'
    URL = '/rescan'
    ARGUMENTS = (
        ['fqdn'],
        ['fqdn', 'option'],
    )

    HELP_SHORT = "Rescan a machine."
    HELP = """Command to rescan machines. Normally all machines are scanned once a day
automatically. For some reason it makes sense to rescan machines manually
immediately, e.g. if new hardware has been added.

Usage:
    RESCAN <fqdn> <option>

Arguments:
    fqdn   - FQDN or hostname of the machine.
    option - Specify what should be rescanned. Options are:

               status            : Check machine status (ping, SSH, login).
               all               : Complete scan.
               misc              : Check miscellaneous software/hardware attributes.
               installations     : Rescan installed distributions only.
               networkinterfaces : Rescan network interfaces only.

Example:
    RESCAN foo.domain.tld networkinterfaces
"""

    @staticmethod
    def get_urls():
        return [
            re_path(r'^rescan$', RescanCommand.as_view(), name='rescan'),
        ]

    @staticmethod
    def get_tabcompletion():
        return MachineCheck.Scan.Action.as_list

    def get(self, request, *args, **kwargs):
        """Return reservation history of machine."""
        fqdn = request.GET.get('fqdn', None)
        option = request.GET.get('option', 'all')

        try:
            result = get_machine(
                fqdn,
                redirect_to='api:rescan',
                data=request.GET
            )
            if isinstance(result, Serializer):
                return result.as_json
            elif isinstance(result, HttpResponseRedirect):
                return result
            machine = result
        except Exception as e:
            return ErrorMessage(str(e)).as_json

        if option == 'ansible':
            task = Ansible([fqdn])
            TaskManager.add(task)
            return Message("OK.").as_json

        elif option not in MachineCheck.Scan.Action.as_list:
            return ErrorMessage("Unknown option '{}'".format(option)).as_json

        try:
            machine.scan(option)
#            task = MachineCheck(fqdn, tasks.MachineCheck.Scan.to_int(option))
#            TaskManager.add(task)

            if not machine.collect_system_information:
                return InfoMessage(
                    "Collecting system information is disabled for this machine."
                ).as_json


        except Exception as e:
            return ErrorMessage(str(e)).as_json

        return Message("OK.").as_json
