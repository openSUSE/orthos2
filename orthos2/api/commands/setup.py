import logging
from typing import TYPE_CHECKING, Any, List, Union

from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import URLPattern, re_path
from rest_framework.request import Request

from orthos2.api.commands.base import BaseAPIView, get_machine
from orthos2.api.serializers.misc import (
    AuthRequiredSerializer,
    ErrorMessage,
    InfoMessage,
    Message,
    Serializer,
)

if TYPE_CHECKING:
    from orthos2.data.models.machine import Machine

logger = logging.getLogger("api")


class SetupCommand(BaseAPIView):

    METHOD = "GET"
    URL = "/setup"
    ARGUMENTS = (["fqdn", "option_or_choice"],)

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
    def get_urls() -> List[URLPattern]:
        return [
            re_path(r"^setup$", SetupCommand.as_view(), name="setup"),
        ]

    @staticmethod
    def get_tabcompletion() -> List[str]:
        return ["list"]

    def _list(self, request: Request, machine: "Machine") -> JsonResponse:
        """Return list of available distributions for `machine`."""
        if not machine.has_setup_capability():
            return InfoMessage("Machine has no setup capability.").as_json

        grouped_records = machine.fqdn_domain.get_setup_records_grouped(
            machine.architecture.name,
        )

        if not grouped_records:
            return ErrorMessage("No setup records found!").as_json

        response = ""

        theader = [{"full": "Available Distributions"}]
        response = {"header": {"type": "TABLE", "theader": theader}, "data": []}  # type: ignore

        for distribution, records in grouped_records.items():
            logger.info("Distros: %s - records: %s", distribution, records)
            for record in records:
                response["data"].append(  # type: ignore
                    {
                        "full": distribution + ":" + record,
                    }
                )

        return JsonResponse(response)

    def _setup(
        self, request: Request, machine: "Machine", distribution: str
    ) -> JsonResponse:
        """Trigger machine setup for `machine` with `distribution`."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        valid = machine.fqdn_domain.is_valid_setup_choice(
            distribution, machine.architecture.name
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
                    message += (
                        " This machine has no remote power - "
                        "a manuall reboot may be required."
                    )

                return Message(message).as_json
            else:
                return ErrorMessage(
                    "Machine has no setup capability! Please contact '{}'.".format(
                        machine.get_support_contact()
                    )
                ).as_json
        except Exception as e:
            return ErrorMessage(str(e)).as_json

    def get(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> Union[JsonResponse, HttpResponseRedirect]:
        """Perform machine setup."""
        fqdn = request.GET.get("fqdn", None)
        option_or_choice = request.GET.get("option_or_choice", None)
        if fqdn is None:
            return ErrorMessage("FQDN of the machine is required.").as_json
        if option_or_choice is None:
            return ErrorMessage("Option or choice for the machine is required.").as_json

        try:
            result = get_machine(fqdn, redirect_to="api:setup", data=request.GET)
            if isinstance(result, Serializer):
                return result.as_json
            elif isinstance(result, HttpResponseRedirect):
                return result
            machine = result
        except Exception as e:
            return ErrorMessage(str(e)).as_json

        if option_or_choice.lower() == "list":
            return self._list(request, machine)
        else:
            choice = option_or_choice
            return self._setup(request, machine, choice)
