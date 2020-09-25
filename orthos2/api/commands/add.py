import json
import logging

from django.conf.urls import url
from django.contrib.auth.models import AnonymousUser, User
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, reverse

from api.commands import BaseAPIView, get_machine
from api.forms import (AnnotationAPIForm, MachineAPIForm, RemotePowerAPIForm, SerialConsoleAPIForm,
                       VirtualMachineAPIForm)
from api.serializers.misc import (AuthRequiredSerializer, ErrorMessage, InfoMessage,
                                  InputSerializer, Message, Serializer)
from data.models import Annotation, Enclosure, Machine, RemotePower, SerialConsole
from utils.misc import add_offset_to_date, format_cli_form_errors

logger = logging.getLogger('api')


class Add:
    MACHINE = 'machine'
    VIRTUALMACHINE = 'virtualmachine'
    SERIALCONSOLE = 'serialconsole'
    ANNOTATION = 'annotation'
    REMOTEPOWER = 'remotepower'

    as_list = [MACHINE, VIRTUALMACHINE, SERIALCONSOLE, ANNOTATION, REMOTEPOWER]


class AddCommand(BaseAPIView):

    METHOD = 'GET'
    URL = '/add'
    ARGUMENTS = (
        ['args*'],
    )

    HELP_SHORT = "Adds information to the database."
    HELP = """Adds items to the database. All information will be queried interactively.

Usage:
    ADD <item> [args*]

Arguments:
    item - Specify the item which should be added. Items are:

             machine                       : Add a machine (superusers only).
             annotation <fqdn>             : Add an annotation to a specific
                                             machine (no bugreports).
             serialconsole <fqdn>          : Add a serial console to a specific
                                             machine (superusers only).
             remotepower <fqdn>            : Add a remote power to a specific
                                             machine (superusers only).
             virtualmachine <architecture> : Add a virtual machine on a specific
                                             architecture.

Example:
    ADD machine
    ADD virtualmachine x86_64
    ADD serialconsole foo.domain.tld
    ADD remotepower foo.domain.tld
    ADD annotation foo.domain.tld
"""

    @staticmethod
    def get_urls():
        return [
            url(r'^add$', AddCommand.as_view(), name='add'),
        ]

    @staticmethod
    def get_tabcompletion():
        return Add.as_list

    def get(self, request, *args, **kwargs):
        """Dispatcher for the 'add' command."""
        arguments = request.GET.get('args', None)

        if arguments:
            arguments = arguments.split()
            item = arguments[0].lower()
            sub_arguments = arguments[1:]
        else:
            return ErrorMessage("Item is missing!").as_json

        if item == Add.VIRTUALMACHINE:
            if len(sub_arguments) != 1:
                return ErrorMessage("Invalid number of arguments for 'virtualmachine'!").as_json

            return redirect('{}?arch={}'.format(reverse('api:vm_add'), sub_arguments[0]))

        elif item == Add.MACHINE:
            if len(sub_arguments) != 0:
                return ErrorMessage("Invalid number of arguments for 'machine'!").as_json

            return redirect(reverse('api:machine_add'))

        elif item == Add.SERIALCONSOLE:
            if len(sub_arguments) != 1:
                return ErrorMessage("Invalid number of arguments for 'serialconsole'!").as_json

            return redirect('{}?fqdn={}'.format(reverse('api:serialconsole_add'), sub_arguments[0]))

        elif item == Add.ANNOTATION:
            if len(sub_arguments) != 1:
                return ErrorMessage("Invalid number of arguments for 'annotation'!").as_json

            return redirect('{}?fqdn={}'.format(reverse('api:annotation_add'), sub_arguments[0]))

        elif item == Add.REMOTEPOWER:
            if len(sub_arguments) != 1:
                return ErrorMessage("Invalid number of arguments for 'remotepower'!").as_json

            return redirect('{}?fqdn={}'.format(reverse('api:remotepower_add'), sub_arguments[0]))

        return ErrorMessage("Unknown item '{}'!".format(item)).as_json


class AddVMCommand(BaseAPIView):

    URL_POST = '/vm/{arch}/add'

    @staticmethod
    def get_urls():
        return [
            url(r'^vm/add', AddVMCommand.as_view(), name='vm_add'),
            url(r'^vm/(?P<architecture>[a-z0-9\.-_]+)/add$', AddVMCommand.as_view(), name='vm_add'),
        ]

    def _get_available_architectures(self):
        """Return list of available architectures for virtual machines."""
        architectures = list(Machine.api.filter(vm_dedicated_host=True).order_by().values_list(
            'architecture__name',
            flat=True
        ).distinct())
        return architectures

    def get(self, request, *args, **kwargs):
        """Return form for adding a virtual machine."""
        architectures = self._get_available_architectures()
        architecture = request.GET.get('arch', None)

        if architecture.lower() not in architectures:
            return Message("Available architectures: {}".format('|'.join(architectures))).as_json

        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        hosts = Machine.api.filter(vm_dedicated_host=True, architecture__name=architecture)
        host = None

        for host_ in hosts:
            if host_.virtualization_api and (host_.get_virtual_machines().count() < host_.vm_max):
                host = host_
                break

        if host is None:
            return ErrorMessage("No virtual machine hosts left!").as_json

        form = VirtualMachineAPIForm(virtualization_api=host.virtualization_api)

        input = InputSerializer(
            form.as_dict(host),
            self.URL_POST.format(arch=architecture),
            form.get_order()
        )
        return input.as_json

    def post(self, request, architecture, *args, **kwargs):
        """Add virtual machine for specific `architecture`."""
        data = json.loads(request.body.decode('utf-8'))['form']

        try:
            host = Machine.api.get(fqdn__iexact=data['host'], vm_dedicated_host=True)
        except Machine.DoesNotExist:
            return ErrorMessage("Host doesn't exist!").as_json
        except Exception as e:
            return ErrorMessage(str(e)).as_json

        if not host.virtualization_api:
            return ErrorMessage("No virtualization API available!").as_json

        form = VirtualMachineAPIForm(data, virtualization_api=host.virtualization_api)

        if form.is_valid():
            try:
                vm = host.virtualization_api.create(**form.cleaned_data)

                vm.reserve(
                    reason='VM of {}'.format(request.user),
                    until=add_offset_to_date(30),
                    user=request.user
                )

                theader = [
                    {'fqdn': 'FQDN'},
                    {'mac_address': 'MAC address'},
                ]
                if vm.vnc['enabled']:
                    theader.append({'vnc': 'VNC'})

                response = {
                    'header': {'type': 'TABLE', 'theader': theader},
                    'data': [{
                        'fqdn': vm.fqdn,
                        'mac_address': vm.mac_address
                    }],
                }
                if vm.vnc['enabled']:
                    response['data'][0]['vnc'] = '{}:{}'.format(host.fqdn, vm.vnc['port'])

                return JsonResponse(response)

            except Exception as e:
                return ErrorMessage(str(e)).as_json

        return ErrorMessage("\n{}".format(format_cli_form_errors(form))).as_json


class AddMachineCommand(BaseAPIView):

    URL_POST = '/machine/add'

    @staticmethod
    def get_urls():
        return [
            url(r'^machine/add', AddMachineCommand.as_view(), name='machine_add'),
        ]

    def get(self, request, *args, **kwargs):
        """Return form for adding a machine."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:
            return ErrorMessage("Only superusers are allowed to perform this action!").as_json

        form = MachineAPIForm()

        input = InputSerializer(
            form.as_dict(),
            self.URL_POST,
            form.get_order()
        )
        return input.as_json

    def post(self, request, *args, **kwargs):
        """Add machine."""
        if not request.user.is_superuser:
            return ErrorMessage("Only superusers are allowed to perform this action!").as_json

        data = json.loads(request.body.decode('utf-8'))['form']
        form = MachineAPIForm(data)

        if form.is_valid():

            cleaned_data = form.cleaned_data
            mac_address = cleaned_data['mac_address']
            del cleaned_data['mac_address']

            new_machine = Machine(**cleaned_data)
            new_machine.mac_address = mac_address
            try:
                new_machine.save()
            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

            return Message('Ok.').as_json

        return ErrorMessage("\n{}".format(format_cli_form_errors(form))).as_json


class AddSerialConsoleCommand(BaseAPIView):

    URL_POST = '/serialconsole/{fqdn}/add'

    @staticmethod
    def get_urls():
        return [
            url(r'^serialconsole/add', AddSerialConsoleCommand.as_view(), name='serialconsole_add'),
            url(
                r'^serialconsole/(?P<fqdn>[a-z0-9\.-]+)/add$',
                AddSerialConsoleCommand.as_view(),
                name='serialconsole_add'
            ),
        ]

    def get(self, request, *args, **kwargs):
        """Return form for adding a machine."""
        fqdn = request.GET.get('fqdn', None)
        try:
            result = get_machine(
                fqdn,
                redirect_to='api:serialconsole_add',
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

        if not request.user.is_superuser:
            return ErrorMessage("Only superusers are allowed to perform this action!").as_json

        if machine.has_serialconsole():
            return InfoMessage("Machine has already a serial console.").as_json

        form = SerialConsoleAPIForm(machine=machine)

        input = InputSerializer(
            form.as_dict(),
            self.URL_POST.format(fqdn=machine.fqdn),
            form.get_order()
        )
        return input.as_json

    def post(self, request, fqdn, *args, **kwargs):
        """Add serial console to machine."""
        if not request.user.is_superuser:
            return ErrorMessage("Only superusers are allowed to perform this action!").as_json

        try:
            result = get_machine(
                fqdn,
                redirect_to='api:serialconsole_add',
                data=request.GET
            )
            if isinstance(result, Serializer):
                return result.as_json
            elif isinstance(result, HttpResponseRedirect):
                return result
            machine = result
        except Exception as e:
            return ErrorMessage(str(e)).as_json

        if machine.has_serialconsole():
            return InfoMessage("Machine has already a serial console.").as_json

        data = json.loads(request.body.decode('utf-8'))['form']
        form = SerialConsoleAPIForm(data, machine=machine)

        if form.is_valid():
            try:
                serialconsole = SerialConsole(**form.cleaned_data)
                serialconsole.save()
            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

            return Message('Ok.').as_json

        return ErrorMessage("\n{}".format(format_cli_form_errors(form))).as_json


class AddAnnotationCommand(BaseAPIView):

    URL_POST = '/annotation/{fqdn}/add'

    @staticmethod
    def get_urls():
        return [
            url(r'^annotation/add', AddAnnotationCommand.as_view(), name='annotation_add'),
            url(
                r'^annotation/(?P<fqdn>[a-z0-9\.-]+)/add$',
                AddAnnotationCommand.as_view(),
                name='annotation_add'
            ),
        ]

    def get(self, request, *args, **kwargs):
        """Return form for adding an annotation."""
        fqdn = request.GET.get('fqdn', None)
        try:
            result = get_machine(
                fqdn,
                redirect_to='api:annotation_add',
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

        form = AnnotationAPIForm(machine=machine)

        input = InputSerializer(
            form.as_dict(),
            self.URL_POST.format(fqdn=machine.fqdn),
            form.get_order()
        )
        return input.as_json

    def post(self, request, fqdn, *args, **kwargs):
        """Add annotation to machine."""
        try:
            result = get_machine(
                fqdn,
                redirect_to='api:annotation_add',
                data=request.GET
            )
            if isinstance(result, Serializer):
                return result.as_json
            elif isinstance(result, HttpResponseRedirect):
                return result
            machine = result
        except Exception as e:
            return ErrorMessage(str(e)).as_json

        data = json.loads(request.body.decode('utf-8'))['form']
        form = AnnotationAPIForm(data, machine=machine)

        if form.is_valid():
            try:
                cleaned_data = form.cleaned_data
                annotation = Annotation(
                    machine_id=machine.pk,
                    reporter=request.user,
                    text=cleaned_data['text']
                )
                annotation.save()
            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

            return Message('Ok.').as_json

        return ErrorMessage("\n{}".format(format_cli_form_errors(form))).as_json


class AddRemotePowerCommand(BaseAPIView):

    URL_POST = '/remotepower/{fqdn}/add'

    @staticmethod
    def get_urls():
        return [
            url(r'^remotepower/add', AddRemotePowerCommand.as_view(), name='remotepower_add'),
            url(
                r'^remotepower/(?P<fqdn>[a-z0-9\.-]+)/add$',
                AddRemotePowerCommand.as_view(),
                name='remotepower_add'
            ),
        ]

    def get(self, request, *args, **kwargs):
        """Return form for adding a remotepower."""
        fqdn = request.GET.get('fqdn', None)
        try:
            result = get_machine(
                fqdn,
                redirect_to='api:remotepower_add',
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

        if not request.user.is_superuser:
            return ErrorMessage("Only superusers are allowed to perform this action!").as_json

        if machine.has_remotepower():
            return InfoMessage("Machine has already a remote power.").as_json

        form = RemotePowerAPIForm(machine=machine)

        input = InputSerializer(
            form.as_dict(),
            self.URL_POST.format(fqdn=machine.fqdn),
            form.get_order()
        )
        return input.as_json

    def post(self, request, fqdn, *args, **kwargs):
        """Add remote power to machine."""
        if not request.user.is_superuser:
            return ErrorMessage("Only superusers are allowed to perform this action!").as_json

        try:
            result = get_machine(
                fqdn,
                redirect_to='api:remotepower_add',
                data=request.GET
            )
            if isinstance(result, Serializer):
                return result.as_json
            elif isinstance(result, HttpResponseRedirect):
                return result
            machine = result
        except Exception as e:
            return ErrorMessage(str(e)).as_json

        if machine.has_remotepower():
            return InfoMessage("Machine has already a remote power.").as_json

        data = json.loads(request.body.decode('utf-8'))['form']
        form = RemotePowerAPIForm(data, machine=machine)

        if form.is_valid():
            try:
                remotepower = RemotePower(**form.cleaned_data)
                remotepower.save()
            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

            return Message('Ok.').as_json

        return ErrorMessage("\n{}".format(format_cli_form_errors(form))).as_json
