from typing import Any, List, Union

from django.http import HttpResponseRedirect, JsonResponse
from django.urls import URLPattern, re_path
from rest_framework.request import Request

from orthos2.api.commands.base import BaseAPIView, get_machine
from orthos2.api.serializers.misc import ErrorMessage, InfoMessage, Message, Serializer
from orthos2.taskmanager.tasks.daily import DailyMachineChecks
from orthos2.taskmanager.tasks.machinetasks import MachineCheck


class RescanCommand(BaseAPIView):

    METHOD = "GET"
    URL = "/rescan"
    ARGUMENTS = (
        ["fqdn"],
        ["fqdn", "option"],
    )

    HELP_SHORT = "Rescan a machine."
    HELP = """Command to rescan machines. Normally all machines are scanned once a day
automatically. For some reason it makes sense to rescan machines manually
immediately, e.g. if new hardware has been added.

Usage:
    RESCAN <fqdn> <option>

Arguments:
    fqdn   - FQDN or hostname of the machine ("all" without option will simulate daily machine check).
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
    def get_urls() -> List[URLPattern]:
        return [
            re_path(r"^rescan$", RescanCommand.as_view(), name="rescan"),
        ]

    @staticmethod
    def get_tabcompletion() -> List[str]:
        return MachineCheck.Scan.Action.as_list

    def get(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> Union[JsonResponse, HttpResponseRedirect]:
        """Return reservation history of machine."""
        fqdn = request.GET.get("fqdn", "")
        option = request.GET.get("option", "all")

        try:
            if fqdn == "all":
                DailyMachineChecks.do_scan_all()
                return Message("OK.").as_json

            result = get_machine(fqdn, redirect_to="api:rescan", data=request.GET)
            if isinstance(result, Serializer):
                return result.as_json
            elif isinstance(result, HttpResponseRedirect):
                return result
            machine = result
        except Exception as e:
            return ErrorMessage(str(e)).as_json

        if option not in MachineCheck.Scan.Action.as_list:
            return ErrorMessage("Unknown option '{}'".format(option)).as_json

        try:
            machine.scan(option)

            if not machine.collect_system_information:
                return InfoMessage(
                    "Collecting system information is disabled for this machine."
                ).as_json

        except Exception as e:
            return ErrorMessage(str(e)).as_json

        return Message("OK.").as_json
