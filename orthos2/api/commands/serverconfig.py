from typing import Any, Dict, List

from django.contrib.auth.models import AnonymousUser
from django.http import JsonResponse
from django.urls import URLPattern, re_path
from rest_framework.request import Request

from orthos2.api.commands.base import BaseAPIView
from orthos2.api.serializers.misc import (
    AuthRequiredSerializer,
    ErrorMessage,
    InfoMessage,
)
from orthos2.data.models import ServerConfig


class ServerConfigCommand(BaseAPIView):

    METHOD = "GET"
    URL = "/serverconfig"
    ARGUMENTS = ([],)

    HELP_SHORT = "Show server configuration."
    HELP = """Show server configuration (superusers only).

Usage:
    CONFIG

Example:
    CONFIG
"""

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^serverconfig$", ServerConfigCommand.as_view(), name="serverconfig"
            ),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Show server configuration."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        config = ServerConfig.objects.all()

        if config.count() == 0:
            return InfoMessage("No configurations available.").as_json

        theader = [{"key": "Key"}, {"value": "Value"}]
        response: Dict[str, Any] = {
            "header": {"type": "TABLE", "theader": theader},
            "data": [],
        }

        for item in config:
            response["data"].append({"key": item.key, "value": item.value})

        return JsonResponse(response)
