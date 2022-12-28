import datetime
import json

from django.urls import re_path
from django.contrib.auth.models import AnonymousUser, User
from django.http import HttpResponseRedirect

from orthos2.utils.misc import add_offset_to_date, format_cli_form_errors
from orthos2.api.commands import BaseAPIView, get_machine
from orthos2.api.forms import ReserveMachineAPIForm
from orthos2.api.serializers.misc import (AuthRequiredSerializer, ErrorMessage,
                                          InputSerializer, Message, Serializer)
from orthos2.data.models import Machine


class ReserveCommand(BaseAPIView):

    METHOD = 'GET'
    URL = '/reserve'
    URL_POST = '/machine/{id}/reserve'
    ARGUMENTS = (
        ['fqdn'],
    )

    HELP_SHORT = "Reserve machines."
    HELP = """Reserves a machine.

Usage:
    RESERVE <fqdn>

Arguments:
    fqdn - FQDN or hostname of the machine.

Example:
    RESERVE foo.domain.tld
"""

    @staticmethod
    def get_urls():
        return [
            re_path(r'^reserve$', ReserveCommand.as_view(), name='reserve'),
            re_path(r'^machine/(?P<id>[0-9]+)/reserve$', ReserveCommand.as_view(), name='reserve'),
        ]

    def get(self, request, *args, **kwargs):
        """Return reservation form for valid machine."""
        fqdn = request.GET.get('fqdn', None)

        try:
            result = get_machine(
                fqdn,
                redirect_to='api:reserve',
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

        form = ReserveMachineAPIForm(
            username=request.user.username,
            reason=machine.reserved_reason
        )

        input = InputSerializer(
            form.as_dict(),
            self.URL_POST.format(id=machine.pk),
            form.get_order()
        )
        return input.as_json

    def post(self, request, id, *args, **kwargs):
        """Process reservation."""
        try:
            machine = Machine.objects.get(pk=id)
        except Machine.DoesNotExist:
            return ErrorMessage("Machine doesn't exist!").as_json

        try:
            data = json.loads(request.body.decode('utf-8'))['form']

            if data['until'] == 0 and request.user.is_superuser:
                # set to 'infinite'
                data['until'] = datetime.date.max
            else:
                # set 'until' field (=offset) to concrete date for form validation
                data['until'] = add_offset_to_date(data['until'], as_string=True)

            form = ReserveMachineAPIForm(data)
        except (KeyError, ValueError):
            return ErrorMessage("Data format is invalid!").as_json

        if form.is_valid():
            reason = form.cleaned_data['reason']
            until = form.cleaned_data['until']
            username = form.cleaned_data['username']

            try:
                user = User.objects.get(username=username)
            except Exception:
                return ErrorMessage("User doesn't exist!").as_json

            try:
                machine.reserve(
                    reason,
                    until,
                    user=request.user,
                    reserve_for_user=user
                )
                return Message('OK.').as_json

            except Exception as e:
                return ErrorMessage(str(e)).as_json
        else:
            return ErrorMessage("\n{}".format(format_cli_form_errors(form))).as_json
