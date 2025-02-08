from typing import Any, List, Union

from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import URLPattern, re_path
from rest_framework.request import Request

from orthos2.api.commands.base import BaseAPIView, get_machine
from orthos2.api.serializers.misc import (
    AuthRequiredSerializer,
    ErrorMessage,
    Message,
    Serializer,
)
from orthos2.data.models import RemotePower


class PowerCommand(BaseAPIView):

    METHOD = "GET"
    URL = "/powercycle"
    ARGUMENTS = (["fqdn", "action"],)

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
    def get_urls() -> List[URLPattern]:
        return [
            re_path(r"^powercycle$", PowerCommand.as_view(), name="powercycle"),
        ]

    @staticmethod
    def get_tabcompletion() -> List[str]:
        return RemotePower.Action.as_list

    def get(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> Union[JsonResponse, HttpResponseRedirect]:
        """Perform machine power cycle."""
        fqdn = request.GET.get("fqdn", "")
        action = request.GET.get("action", "")

        if action.lower() not in RemotePower.Action.as_list:
            return ErrorMessage("Unknown action '{}'!".format(action)).as_json

        try:
            result = get_machine(fqdn, redirect_to="api:powercycle", data=request.GET)
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
            result = machine.powercycle(action.lower(), user=request.user)  # type: ignore

            if action.lower() == RemotePower.Action.STATUS:
                return Message(
                    "Status: {} ({})".format(
                        result.capitalize(), machine.remotepower.name  # type: ignore
                    )
                ).as_json

            if result:
                return Message("OK.").as_json
            else:
                return ErrorMessage("Something went wrong!").as_json

        except Exception as e:
            return ErrorMessage(str(e)).as_json

        return ErrorMessage("Something went wrong!").as_json
