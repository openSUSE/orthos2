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


class ReleaseCommand(BaseAPIView):

    METHOD = "GET"
    URL = "/release"
    ARGUMENTS = (["fqdn"],)

    HELP_SHORT = "Release machines."
    HELP = """Releases a machine.

Usage:
    RELEASE <machine>

Arguments:
    machine - FQDN or hostname of the machine.

Example:
    RELEASE foo.domain.tld
"""

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(r"^release$", ReleaseCommand.as_view(), name="release"),
        ]

    def get(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> Union[JsonResponse, HttpResponseRedirect]:
        """Release a machine."""
        fqdn = request.GET.get("fqdn", None)
        if fqdn is None:
            return ErrorMessage("fqdn is required").as_json

        try:
            result = get_machine(fqdn, redirect_to="api:release", data=request.GET)
            if isinstance(result, Serializer):
                return result.as_json
            elif isinstance(result, HttpResponseRedirect):
                return result
            machine = result
        except Exception as e:
            return ErrorMessage(str(e)).as_json

        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        try:
            machine.release(user=request.user)
            return Message("OK.").as_json
        except Exception as e:
            return ErrorMessage(str(e)).as_json
