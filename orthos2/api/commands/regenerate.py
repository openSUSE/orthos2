from django.conf.urls import url
from django.contrib.auth.models import AnonymousUser, User
from django.http import HttpResponseRedirect

from api.commands import BaseAPIView, get_machine
from api.serializers.misc import (AuthRequiredSerializer, ErrorMessage,
                                  Message, Serializer)
from data.models import SerialConsole
from data.signals import (signal_cobbler_regenerate,
                          signal_serialconsole_regenerate)


class Regenerate:
    MOTD = 'motd'
    COBBLER = 'cobbler'
    SERIALCONSOLE = 'serialconsole'

    as_list = [MOTD, COBBLER, SERIALCONSOLE]


class RegenerateCommand(BaseAPIView):

    METHOD = 'GET'
    URL = '/regenerate'
    ARGUMENTS = (
        ['fqdn', 'option'],
        ['service']
    )

    HELP_SHORT = "Regenerate machine-related or service files."
    HELP = """Command to regenerate machine-related files or configuration files for various
services.

Usage:
    REGENERATE <fqdn> <option>
    REGENERATE <service>

Arguments:
    fqdn    - FQDN or hostname of the machine.
    option  - Specify what machine-related file should be regenerated.
                Options are:

                  motd          : Message of the day.

    service - Specify which service configuration file shoud be regenerated.
                Options are:

                  cobbler          : Cobbler configuration (superusers only).
                  serialconsole : Serial console files (superusers only).

Example:
    REGENERATE foo.domain.tld motd
    REGENERATE cobbler
"""

    @staticmethod
    def get_urls():
        return [
            url(r'^regenerate$', RegenerateCommand.as_view(), name='regenerate'),
        ]

    @staticmethod
    def get_tabcompletion():
        return Regenerate.as_list

    def get(self, request, *args, **kwargs):
        """
        Trigger regeneration of machine-related/service files.
        """
        fqdn = request.GET.get('fqdn', None)
        option = request.GET.get('option', None)
        service = request.GET.get('service', None)

        if service and (service.lower() in [Regenerate.COBBLER, Regenerate.SERIALCONSOLE]):
            if isinstance(request.user, AnonymousUser) or not request.auth:
                return AuthRequiredSerializer().as_json

            if not request.user.is_superuser:
                return ErrorMessage("Only superusers are allowed to perform this action!").as_json

            # regenerate Cobbler entries
            if service.lower() == Regenerate.COBBLER:
                signal_cobbler_regenerate.send(sender=None, domain_id=None)
                return Message("Regenerate Cobbler entries...").as_json

            # regenerate serial console entries iterating over all cscreen servers
            elif service.lower() == Regenerate.SERIALCONSOLE:
                machines = SerialConsole.objects.all().values_list(
                    'cscreen_server__fqdn', flat=True
                )

                for fqdn in machines.distinct():
                    signal_serialconsole_regenerate.send(sender=None, cscreen_server_fqdn=fqdn)

                return Message("Regenerate serial console entries...").as_json

        elif (fqdn is not None) and (option is not None):
            try:
                result = get_machine(
                    fqdn,
                    redirect_to='api:regenerate',
                    data=request.GET
                )
                if isinstance(result, Serializer):
                    return result.as_json
                elif isinstance(result, HttpResponseRedirect):
                    return result
                machine = result
            except Exception as e:
                return ErrorMessage(str(e)).as_json

            if option.lower() not in [Regenerate.MOTD]:
                return ErrorMessage("Unknown option '{}'!".format(option)).as_json

            if isinstance(request.user, AnonymousUser) or not request.auth:
                return AuthRequiredSerializer().as_json

            try:
                if option.lower() == Regenerate.MOTD:
                    machine.update_motd(user=request.user)
                    return Message("OK.").as_json
            except Exception as e:
                return ErrorMessage(str(e)).as_json

        return ErrorMessage("Unknown service '{}'!".format(service)).as_json
