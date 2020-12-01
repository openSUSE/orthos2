from orthos2.api.commands import BaseAPIView, get_machine
from orthos2.api.serializers.misc import (AuthRequiredSerializer, ErrorMessage,
                                          InfoMessage, Message, Serializer)
from django.conf.urls import re_path
from django.contrib.auth.models import AnonymousUser, User
from django.http import HttpResponseRedirect, JsonResponse

import logging
logger = logging.getLogger('api')

class SetupCommand(BaseAPIView):

    METHOD = 'GET'
    URL = '/setup'
    ARGUMENTS = (
        ['fqdn', 'option_or_choice'],
    )

    HELP_SHORT = "Automatic machine setup."
    HELP = """Command to setup (re-install) a machine.

Usage:
    SETUP <fqdn> list
    SETUP <fqdn> <choice>

Arguments:
    machine - FQDN or hostname of the machine.
    choice  - Distribution setup which should be applied/installed.

Example:
    SETUP foo.suse.de list
    SETUP foo.suse.de SLE12-SP2-install-auto
"""

    @staticmethod
    def get_urls():
        return [
            re_path(r'^setup$', SetupCommand.as_view(), name='setup'),
        ]

    @staticmethod
    def get_tabcompletion():
        return ['list']

    def _list(self, request, machine):
        """Return list of available distributions for `machine`."""
        machinegroup = None
        if not machine.has_setup_capability():
            return InfoMessage("Machine has no setup capability.").as_json

        if machine.group and not machine.group.setup_use_architecture:
            machinegroup = machine.group.name

        grouped_records = machine.fqdn_domain.get_setup_records(
            machine.architecture.name,
            machinegroup=machinegroup
        )

        if not grouped_records:
            return ErrorMessage("No setup records found!").as_json

        response = ''

        theader = [
            {'full': 'Available Distributions'}
        ]
        response = {
            'header': {'type': 'TABLE', 'theader': theader},
            'data': []
        }

        for distribution, records in grouped_records.items():
            logger.info("Distros: {} - records: {}".format(distribution, records))
            for record in records:
                response['data'].append(
                    {
                        'full': distribution + ':' + record,
                    }
                )

        return JsonResponse(response)

    def _setup(self, request, machine, distribution):
        """Trigger machine setup for `machine` with `distribution`."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        machinegroup = None
        if machine.group and not machine.group.setup_use_architecture:
            machinegroup = machine.group.name

        valid = machine.fqdn_domain.is_valid_setup_choice(
            distribution,
            machine.architecture.name,
            machinegroup=machinegroup
        )

        if not valid:
            return ErrorMessage(
                "Unknown choice '{}'! Use 'SETUP <fqdn> list'.".format(distribution)
            ).as_json

        try:
            result = machine.setup(distribution)

            if result:
                message = "OK."

                if not machine.has_remotepower():
                    message += " This machine has no remote power - "\
                        "a manuall reboot may be required."

                return Message(message).as_json
            else:
                return ErrorMessage(
                    "Machine has no setup capability! Please contact '{}'.".format(
                        machine.get_support_contact()
                    )
                ).as_json
        except Exception as e:
            return ErrorMessage(str(e)).as_json

    def get(self, request, *args, **kwargs):
        """Perform machine setup."""
        fqdn = request.GET.get('fqdn', None)
        option_or_choice = request.GET.get('option_or_choice', None)
        choice = None

        try:
            result = get_machine(
                fqdn,
                redirect_to='api:setup',
                data=request.GET
            )
            if isinstance(result, Serializer):
                return result.as_json
            elif isinstance(result, HttpResponseRedirect):
                return result
            machine = result
        except Exception as e:
            return ErrorMessage(str(e)).as_json

        if option_or_choice.lower() == 'list':
            return self._list(request, machine)
        else:
            choice = option_or_choice
            return self._setup(request, machine, choice)

        return ErrorMessage("Something went wrong!").as_json
