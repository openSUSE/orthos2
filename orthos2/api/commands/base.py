from django.shortcuts import redirect
from rest_framework.views import APIView

from api.serializers.misc import SelectSerializer
from data.models import Machine


def get_machine(fqdn, redirect_to, data=None, redirect_key_replace='fqdn'):
    """
    Look up FQDN in the database and return one machine object if found or raise corresponding
    exception if something went wrong.

    The hostname is often sufficient for the lookup, so try the hostname (hostname + '.') first.
    """
    if not fqdn:
        raise ValueError("Requires <fqdn> argument!")

    try:
        machines = [Machine.api.get(fqdn__startswith=fqdn + '.')]
    except Exception:
        machines = list(Machine.api.filter(fqdn__startswith=fqdn))

    if len(machines) == 1:
        machine = machines[0]

    elif len(machines) == 0:
        raise Exception("Machine '{}' does not exist!".format(fqdn))

    else:
        selection = SelectSerializer(machines, 'Please specify:')
        return selection

    if fqdn != machine.fqdn:
        response = redirect(redirect_to)

        if data:
            if redirect_key_replace is not None:
                data = data.copy()
                data.__setitem__(redirect_key_replace, machine.fqdn)
            response['Location'] += '?{}'.format(data.urlencode())

        return response

    return machine


class BaseAPIView(APIView):

    @staticmethod
    def get_urls():
        raise NotImplementedError

    @staticmethod
    def get_tabcompletion():
        return []

    @classmethod
    def description(cls):
        return {
            'help': cls.HELP_SHORT,
            'docstring': cls.HELP,
            'tabcompletion': cls.get_tabcompletion(),
            'url': cls.URL,
            'arguments': cls.ARGUMENTS,
            'method': cls.METHOD
        }
