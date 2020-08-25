from django.conf.urls import re_path
from django.contrib.auth.models import AnonymousUser, User
from django.http import HttpResponseRedirect

from api.commands import BaseAPIView, get_machine
from api.serializers.misc import (AuthRequiredSerializer, ErrorMessage,
                                  Message, Serializer)
from data.models import RemotePower


class PowerCommand(BaseAPIView):

    METHOD = 'GET'
    URL = '/powercycle'
    ARGUMENTS = (
        ['fqdn', 'action'],
    )

    HELP_SHORT = "Power cycles a machine."
    HELP = """Command to power cycle machines or the get the current status.

Usage:
    POWER <fqdn> <action>

Arguments:
    fqdn   - FQDN or hostname of the machine.
    action - Specify new power state. Actions are:

               on                 : Power on.
               off                : Power off via SSH. If didn't succeed, use remote power.
               off-ssh            : Power off via SSH only.
               off-remotepower    : Power off via remote power only.
               reboot             : Reboot via SSH. If didn't succeed, use remote power.
               reboot-ssh         : Reboot via SSH only.
               reboot-remotepower : Reboot via remote power only.
               status             : Get power status.

Example:
    POWER foo.domain.tld reboot
"""

    @staticmethod
    def get_urls():
        return [
            re_path(r'^powercycle$', PowerCommand.as_view(), name='powercycle'),
        ]

    @staticmethod
    def get_tabcompletion():
        return RemotePower.Action.as_list

    def get(self, request, *args, **kwargs):
        """
        Perform machine power cycle.
        """
        fqdn = request.GET.get('fqdn', None)
        action = request.GET.get('action', None)

        if action.lower() not in RemotePower.Action.as_list:
            return ErrorMessage("Unknown action '{}'!".format(action)).as_json

        try:
            result = get_machine(
                fqdn,
                redirect_to='api:powercycle',
                data=request.GET
            )
            if isinstance(result, Serializer):
                return result.as_json
            elif isinstance(result, HttpResponseRedirect):
                return result
            machine = result
        except Exception as e:
            return ErrorMessage(str(e)).as_json

        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not machine.has_remotepower():
            return ErrorMessage("Machine has no remote power!").as_json

        try:
            result = machine.powercycle(action.lower(), user=request.user)

            if action.lower() == RemotePower.Action.STATUS:
                return Message("Status: {} ({})".format(
                    result.capitalize(),
                    machine.remotepower.name
                )).as_json

            if result:
                return Message("OK.").as_json
            else:
                return ErrorMessage("Something went wrong!").as_json

        except Exception as e:
            return ErrorMessage(str(e)).as_json

        return ErrorMessage("Something went wrong!").as_json
