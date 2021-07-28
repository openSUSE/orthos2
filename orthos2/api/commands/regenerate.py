from orthos2.api.commands import BaseAPIView, get_machine
from orthos2.api.serializers.misc import (AuthRequiredSerializer, ErrorMessage,
                                          Message, Serializer)
from orthos2.data.models import SerialConsole
from orthos2.data.signals import (signal_cobbler_regenerate,
                                  signal_serialconsole_regenerate)
from orthos2.utils.misc import get_domain
from orthos2.data.models import Domain

from django.conf.urls import re_path
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponseRedirect


class RegenerateCommand(BaseAPIView):

    METHOD = 'GET'
    URL = '/regenerate'
    ARGUMENTS = (
        ['service'],
        ['service', 'fqdn'],
    )

    MOTD = 'motd'
    COBBLER = 'cobbler'
    SERIALCONSOLE = 'serialconsole'

    SERVICES = [MOTD, COBBLER, SERIALCONSOLE]

    HELP_SHORT = "Regenerate machine-related or service files."
    HELP = """Command to regenerate machine-related files or configuration files for various
services (superusers only).

Usage:
    REGENERATE <service> [ <fqdn> ]

Arguments:
    service - Specify which service configuration file shoud be regenerated.
              Without passing fqdn parameter, all hosts/servers are synced.
        Options are:
            motd          : Message of the day.
            cobbler       : Cobbler configuration (superusers only).
            serialconsole : Serial console files (superusers only).

    fqdn    - FQDN or hostname of the machine/server.
              Passing this optional parameter restricts above service
              to specific hosts or servers:

            motd          : Hostname for which /etc/motd is regenerated
            cobbler       : Cobbler server configuration which is synced with orthos.
            serialconsole : Serial console server which is synced

Example:
    REGENERATE cobbler
    REGENERATE cobbler hudba2.arch.suse.cz
    REGENERATE serialconsole sconsole1.arch.suse.de
    REGENERATE motd foo.domain.tld
"""

    @staticmethod
    def get_urls():
        return [
            re_path(r'^regenerate$', RegenerateCommand.as_view(), name='regenerate'),
        ]

    @classmethod
    def get_tabcompletion(cls):
        return cls.SERVICES

    def get(self, request, *args, **kwargs):
        """Trigger regeneration of machine-related/service files."""
        service = request.GET.get('service', None)
        fqdn = request.GET.get('fqdn', None)
        machine = None

        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:
            return ErrorMessage("Only superusers are allowed to perform this action!").as_json

        if not service:
            return ErrorMessage("Service not set").as_json

        if fqdn:
            try:
                machine = get_machine(
                    fqdn,
                    redirect_to='api:regenerate',
                    data=request.GET
                )
                if not machine:
                    return ErrorMessage("machine {} not found".format(fqdn)).as_json
                if isinstance(machine, Serializer):
                    return machine.as_json
                elif isinstance(machine, HttpResponseRedirect):
                    return machine
            except Exception as e:
                return ErrorMessage(str(e)).as_json

        # regenerate Cobbler entries
        if service.lower() == RegenerateCommand.COBBLER:
            domain_id = None
            if fqdn:
                domain = get_domain(fqdn)
                if not domain:
                    return ErrorMessage("No domain found for machine: " + fqdn).as_json
                o_domain = Domain.objects.get(name=domain)
                if not o_domain:
                    return ErrorMessage("No orthos domain found for domain: " + domain).as_json
                domain_id = getattr(o_domain, 'id', None)
                if not domain_id:
                    return ErrorMessage("Could not find id for orthos domain: " + domain).as_json
                msg = 'domain ' + domain
            else:
                domain = None
                msg = 'all domains'
            signal_cobbler_regenerate.send(sender=None, domain_id=domain_id)
            return Message("Regenerate Cobbler entries for " + msg).as_json

        # regenerate serial console entries iterating over all cscreen servers
        elif service.lower() == RegenerateCommand.SERIALCONSOLE:
            machines = Domain.objects.all().values_list(
                'cscreen_server__fqdn', flat=True
            )
            if fqdn:
                if fqdn in machines.distinct():
                    signal_serialconsole_regenerate.send(sender=None, cscreen_server_fqdn=fqdn)
                    msg = fqdn
                else:
                    return ErrorMessage("Not a serial console server: " + fqdn).as_json
            else:
                msg = ''
                for fqdn in machines.distinct():
                    signal_serialconsole_regenerate.send(sender=None, cscreen_server_fqdn=fqdn)
                    msg += ' ' + fqdn
            return Message("Regenerated serial console entries for serial console servers: "
                           + msg).as_json

        # regenerate MOTD (only works per machine atm)
        elif service.lower() == RegenerateCommand.MOTD:
            if not fqdn:
                return Message("regenerte motd needs fqdn parameter").as_json
            machine.update_motd(user=request.user)
            return Message("OK.").as_json
        else:
            return ErrorMessage("Unknown service {}".format(service)).as_json

        return ErrorMessage("Unknown error - params: {} - {}".format(service, fqdn)).as_json
