from django.conf.urls import url
from django.contrib.auth.models import AnonymousUser, User
from django.http import HttpResponseRedirect

from api.commands import BaseAPIView, get_machine
from api.serializers.misc import AuthRequiredSerializer, ErrorMessage, Message, Serializer


class ReleaseCommand(BaseAPIView):

    METHOD = 'GET'
    URL = '/release'
    ARGUMENTS = (
        ['fqdn'],
    )

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
    def get_urls():
        return [
            url(r'^release$', ReleaseCommand.as_view(), name='release'),
        ]

    def get(self, request, *args, **kwargs):
        """
        Release a machine.
        """
        fqdn = request.GET.get('fqdn', None)

        try:
            result = get_machine(
                fqdn,
                redirect_to='api:release',
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

        try:
            machine.release(user=request.user)
            return Message('OK.').as_json
        except Exception as e:
            return ErrorMessage(str(e)).as_json
