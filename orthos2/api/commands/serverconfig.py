from django.conf.urls import url
from django.contrib.auth.models import AnonymousUser, User
from django.http import JsonResponse

from api.commands import BaseAPIView, get_machine
from api.serializers.misc import AuthRequiredSerializer, ErrorMessage, InfoMessage
from data.models import ServerConfig


class ServerConfigCommand(BaseAPIView):

    METHOD = 'GET'
    URL = '/serverconfig'
    ARGUMENTS = (
        [],
    )

    HELP_SHORT = "Show server configuration."
    HELP = """Show server configuration (superusers only).

Usage:
    CONFIG

Example:
    CONFIG
"""

    @staticmethod
    def get_urls():
        return [
            url(r'^serverconfig$', ServerConfigCommand.as_view(), name='serverconfig'),
        ]

    def get(self, request, *args, **kwargs):
        """
        Show server configuration.
        """
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:
            return ErrorMessage("Only superusers are allowed to perform this action!").as_json

        config = ServerConfig.objects.all()

        if config.count() == 0:
            return InfoMessage("No configurations available.").as_json

        theader = [
            {'key': 'Key'},
            {'value': 'Value'}
        ]
        response = {
            'header': {'type': 'TABLE', 'theader': theader},
            'data': []
        }

        for item in config:
            response['data'].append(
                {
                    'key': item.key,
                    'value': item.value
                }
            )

        return JsonResponse(response)
