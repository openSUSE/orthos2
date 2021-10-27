import json

from orthos2.api.commands import BaseAPIView
from orthos2.api.models import APIQuery
from orthos2.api.serializers.misc import ErrorMessage, InfoMessage
from django.conf.urls import re_path
from django.http import JsonResponse


class QueryCommand(BaseAPIView):

    METHOD = 'POST'
    URL = '/query'
    ARGUMENTS = (
        ['data*'],
    )

    HELP_SHORT = "Retrieve information about a machine."
    HELP = """Command to query machines. You can just specify a comma-separated list of
fields, then you get that fields for all machines.

Example:

    QUERY fqdn, cpu_physical
    QUERY fqdn WHERE cpu_model =~ Intel
    QUERY fqdn WHERE cpu_model =~ Intel OR !efi

Valid operators are:
------------------------------------------------------------------------------
!<field>            not
== =                exactly equal
=~                  contains
=*                  startswith
!=                  unequal
>  <                greater or less than (numbers only)
>= <=               greater equals or less equals (numbers only)
AND                 logical conjunction
OR                  logical disjunction
------------------------------------------------------------------------------
"""

    @staticmethod
    def get_urls():
        return [
            re_path(r'^query$', QueryCommand.as_view(), name='query'),
        ]

    @staticmethod
    def get_tabcompletion():
        return APIQuery.get_tab_completion_options()

    def post(self, request, *args, **kwargs):
        """Return query result."""
        response = {}

        try:
            query_str = json.loads(request.body.decode('utf-8'))['data']
        except (KeyError, ValueError):
            return ErrorMessage("Data format is invalid!").as_json

        try:
            query = APIQuery(query_str)
            query.execute(user=request.user)
        except APIQuery.EmptyResult as e:
            return InfoMessage(str(e)).as_json
        except Exception as e:
            return ErrorMessage(str(e)).as_json

        response['header'] = {'type': 'TABLE', 'theader': query.get_theader()}
        response['data'] = query.data

        return JsonResponse(response, safe=False)
