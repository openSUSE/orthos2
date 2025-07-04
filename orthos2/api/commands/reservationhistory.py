from typing import Any, Dict, List, Union

from django.http import HttpResponseRedirect, JsonResponse
from django.urls import URLPattern, re_path
from rest_framework.request import Request

from orthos2.api.commands.base import BaseAPIView, get_machine
from orthos2.api.serializers.misc import ErrorMessage, InfoMessage, Serializer
from orthos2.data.models import ReservationHistory


class ReservationHistoryCommand(BaseAPIView):

    METHOD = "GET"
    URL = "/reservationhistory"
    ARGUMENTS = (["fqdn"],)

    HELP_SHORT = "Show reservation history of a machine."
    HELP = """Show reservation history of a machine.

Usage:
    RESERVATIONHISTORY <machine>

Arguments:
    machine - FQDN or hostname of the machine.

Example:
    RESERVATIONHISTORY foo.domain.tld
"""

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^reservationhistory$",
                ReservationHistoryCommand.as_view(),
                name="history",
            ),
        ]

    def get(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> Union[JsonResponse, HttpResponseRedirect]:
        """Return reservation history of machine."""
        fqdn = request.GET.get("fqdn", "")

        try:
            result = get_machine(fqdn, redirect_to="api:history", data=request.GET)
            if isinstance(result, Serializer):
                return result.as_json
            elif isinstance(result, HttpResponseRedirect):
                return result
            machine = result
        except Exception as e:
            return ErrorMessage(str(e)).as_json

        history = ReservationHistory.objects.filter(machine__fqdn=machine.fqdn)  # type: ignore

        if history.count() == 0:
            return InfoMessage("No history available yet.").as_json

        theader = [
            {"user": "User"},
            {"at": "Reserved at"},
            {"until": "Reserved until"},
            {"reason": "Reason"},
        ]
        response: Dict[str, Any] = {
            "header": {"type": "TABLE", "theader": theader},
            "data": [],
        }

        for item in history:
            response["data"].append(
                {
                    "user": item.reserved_by,
                    "at": item.reserved_at,
                    "until": item.reserved_until,
                    "reason": item.reserved_reason.replace("\n", ""),
                }
            )

        return JsonResponse(response)
