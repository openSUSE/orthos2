import logging

from orthos2.data.models import (Architecture, Enclosure, Machine, MachineGroup,
                                 NetworkInterface, RemotePower, SerialConsole,
                                 SerialConsoleType, System, is_unique_mac_address,
                                 validate_dns, validate_mac_address)
from orthos2.data.models.domain import validate_domain_ending
from django import forms
from django.forms.models import ModelChoiceIteratorValue
from django.core.validators import MaxValueValidator, MinValueValidator
from django.forms import inlineformset_factory
from django.forms.fields import (BooleanField, CharField, ChoiceField,
                                 DateField, DecimalField, IntegerField)
from django.template.defaultfilters import slugify
from orthos2.frontend.forms import ReserveMachineForm, VirtualMachineForm
from orthos2.utils.misc import DHCPRecordOption
from orthos2.utils.remotepowertype import get_remote_power_type_choices
logger = logging.getLogger('api')


class BaseAPIForm:

    def form_field_to_dict(self, form_field, name, prompt=None, initial=None, required=None):
        """
        Generate and returns a corresponding dictionary for django form fields.

        Available form fields:

            CharField
            DateField
            BooleanField
            DecimalField
            ChoiceField
        """
        if not prompt:
            prompt = form_field.label if form_field.label else name.capitalize()

        if not initial:
            if form_field.initial is not None:
                if isinstance(form_field, BooleanField):
                    initial = 'y' if form_field.initial else 'n'
                else:
                    initial = str(form_field.initial)
            else:
                initial = None

        if not required:
            required = form_field.required

        field = {
            'prompt': prompt,
            'initial': initial,
            'required': required
        }

        if isinstance(form_field, CharField):
            field['type'] = 'STRING'

        elif isinstance(form_field, DateField):
            field['type'] = 'DATE'

        elif isinstance(form_field, BooleanField):
            field['type'] = 'BOOLEAN'

        elif isinstance(form_field, (DecimalField, IntegerField)):
            field['type'] = 'INTEGER'
            field['max'] = form_field.max_value
            field['min'] = form_field.min_value

        elif isinstance(form_field, ChoiceField):
            field['type'] = 'SELECTION'
            field['items'] = []

            for choice in form_field.choices:
                if isinstance(choice[0], ModelChoiceIteratorValue):
                    field['items'].append(
                        {slugify(choice[0].value): {'label': choice[1], 'value': choice[0].value}}
                    )
                else:
                    field['items'].append(
                        {slugify(choice[0]): {'label': choice[1], 'value': choice[0]}}
                    )

        return field

    def as_dict(self):
        """Generate and return form as dictionary."""
        result = {}

        for name, field in self.fields.items():

            result[name] = self.form_field_to_dict(
                field,
                name
            )

        return result


class ReserveMachineAPIForm(ReserveMachineForm, BaseAPIForm):

    def as_dict(self):
        """Generate and return form as dictionary."""
        result = {}

        for name, field in self.fields.items():

            result[name] = self.form_field_to_dict(
                field,
                name
            )

        result['until']['prompt'] = 'Duration (days)'
        result['until']['type'] = 'INTEGER'

        result['username'] = {
            'type': 'STRING',
            'prompt': 'User for which you want to reserve',
            'initial': self.fields['username'].initial,
            'required': True
        }
        return result

    def get_order(self):
        """Return input order."""
        return ['username', 'reason', 'until']


class VirtualMachineAPIForm(VirtualMachineForm, BaseAPIForm):

    def as_dict(self, host):
        """Generate and return form as dictionary."""
        result = {}

        for name, field in self.fields.items():

            result[name] = self.form_field_to_dict(
                field,
                name
            )

        result['host'] = {
            'type': 'STRING',
            'prompt': 'Host FQDN',
            'initial': host.fqdn,
            'required': True
        }

        return result

    def get_order(self):
        """Return input order."""
        return [
            'host',
            'system',
            'architecture',
            'ram_amount',
            'image',
            'disk_size',
            'networkinterfaces',
            'uefi_boot',
            'vnc',
            'parameters'
        ]


class MachineAPIForm(forms.Form, BaseAPIForm):

    def get_architectures():
        """Return architectures choice tuple."""
        architectures = []
        for architecture in Architecture.objects.all().values('id', 'name'):
            architectures.append((architecture['id'], architecture['name']))
        return (architectures)

    def get_systems():
        """Return systems choice tuple."""
        systems = []
        for system in System.objects.all().values('id', 'name'):
            systems.append((system['id'], system['name']))
        return (systems)

    def get_machinegroups():
        """Return machine group choice tuple."""
        groups = [('none', 'None')]
        for group in MachineGroup.objects.all().values('id', 'name'):
            groups.append((group['id'], group['name']))
        return (groups)

    def clean_fqdn(self):
        """Check whether `fqdn` already exists."""
        fqdn = self.cleaned_data['fqdn']
        if Machine.objects.filter(fqdn__iexact=fqdn).count() != 0:
            self.add_error('fqdn', "FQDN is already in use!")
        return fqdn

    def clean_mac_address(self):
        """Check whether `mac_address` already exists."""
        mac_address = self.cleaned_data['mac_address']
        if not is_unique_mac_address(mac_address):
            self.add_error(
                'mac_address',
                "MAC address '{}' is already used by '{}'!".format(
                    mac_address,
                    NetworkInterface.objects.get(mac_address=mac_address).machine.fqdn
                )
            )
        return mac_address

    def clean_enclosure(self):
        """Set the proper `enclosure` value."""
        enclosure = self.cleaned_data['enclosure']
        if not enclosure:
            enclosure = None
        return enclosure

    def clean_group_id(self):
        """Set `group_id` to None if 'None' is selected."""
        group_id = self.cleaned_data['group_id']
        if group_id == 'none':
            group_id = None
        return group_id

    def clean(self):
        """
        Get or create the enclosure.

        Only allow collect system information if connectivity is set to `Full`.
        """
        cleaned_data = super(MachineAPIForm, self).clean()

        enclosure = cleaned_data['enclosure']
        if enclosure:
            try:
                enclosure, created = Enclosure.objects.get_or_create(name=enclosure)
            except Exception as e:
                logger.exception(e)
                self.add_error('enclosure', "Something went wrong!")
        cleaned_data['enclosure'] = enclosure

        check_connectivity = int(cleaned_data['check_connectivity'])
        collect_system_information = cleaned_data['collect_system_information']

        if collect_system_information and check_connectivity != Machine.Connectivity.ALL:
            self.add_error('collect_system_information', "Needs full connectivity check!")

        return cleaned_data

    fqdn = forms.CharField(
        label='FQDN',
        max_length=200,
        validators=[validate_dns, validate_domain_ending],
    )

    enclosure = forms.CharField(
        max_length=200,
        required=False,
    )

    mac_address = forms.CharField(
        label='MAC address',
        validators=[validate_mac_address]
    )

    architecture_id = forms.ChoiceField(
        label='Architecture',
        choices=get_architectures,
    )

    system_id = forms.ChoiceField(
        label='System',
        choices=get_systems,
    )

    group_id = forms.ChoiceField(
        label='Machine group',
        choices=get_machinegroups,
        initial=0,
    )

    nda = forms.BooleanField(
        label='NDA hardware',
        required=False,
        initial=False,
    )

    administrative = forms.BooleanField(
        label='Administrative machine',
        required=False,
        initial=False,
    )

    check_connectivity = forms.ChoiceField(
        label='Check connectivity',
        choices=Machine.CONNECTIVITY_CHOICE,
        initial=Machine.Connectivity.ALL,
    )

    collect_system_information = forms.BooleanField(
        label='Collect system information',
        required=False,
        initial=True,
    )

    dhcpv4_write = forms.ChoiceField(
        label='Write DHCPv4',
        choices=DHCPRecordOption.CHOICE,
        initial=DHCPRecordOption.WRITE,
    )

    dhcpv6_write = forms.ChoiceField(
        label='Write DHCPv6',
        choices=[
            DHCPRecordOption.CHOICE[0],
            DHCPRecordOption.CHOICE[2],
        ],
        initial=DHCPRecordOption.WRITE,
    )
    hypervisor_fqdn = forms.CharField(
        label='Hypervisor',
        max_length=256,
        required=False,
    )

    def get_order(self):
        """Return input order."""
        return [
            'fqdn',
            'enclosure',
            'mac_address',
            'architecture_id',
            'system_id',
            'group_id',
            'hypervisor_fqdn',
            'nda',
            'administrative',
            'check_connectivity',
            'collect_system_information',
            'dhcpv4_write',
            'dhcpv6_write',
        ]


class DeleteMachineAPIForm(forms.Form, BaseAPIForm):

    def clean_fqdn(self):
        """Check whether `fqdn` already exists."""
        fqdn = self.cleaned_data['fqdn']
        if Machine.objects.filter(fqdn__iexact=fqdn).count() == 0:
            self.add_error('fqdn', "FQDN does not exist!")
        return fqdn

    fqdn = forms.CharField(
        label='FQDN',
        max_length=200,
    )

    def get_order(self):
        """Return input order."""
        return [
            'fqdn',
        ]


class SerialConsoleAPIForm(forms.Form, BaseAPIForm):

    def __init__(self, *args, **kwargs):
        machine = kwargs.pop('machine', None)
        self.machine = machine

        super(SerialConsoleAPIForm, self).__init__(*args, **kwargs)

        self._query_fields = (
            'type',
            'baud_rate',
            'kernel_device',
            'kernel_device_num',
            'console_server',
            'port',
            'command',
            'comment',
        )

        SerialConsoleFormSet = inlineformset_factory(
            Machine,
            SerialConsole,
            fields=self._query_fields,
            fk_name='machine'
        )
        formset = SerialConsoleFormSet(instance=machine)

        self.fields = formset.form().fields
        self.fields['type'].empty_label = None
        self.fields['baud_rate'].initial = 5
        self.fields['kernel_device_num'].min_value = 0
        self.fields['kernel_device_num'].max_value = 1024
        self.fields['console_server'].empty_label = 'None'

    def clean(self):
        """Add the machine to cleaned data for further processing."""
        cleaned_data = super(SerialConsoleAPIForm, self).clean()
        cleaned_data['machine'] = self.machine
        serialconsole = SerialConsole(**cleaned_data)
        serialconsole.clean()
        return cleaned_data

    def get_order(self):
        """Return input order."""
        return self._query_fields


class DeleteSerialConsoleAPIForm(forms.Form, BaseAPIForm):

    def clean_fqdn(self):
        """Check whether `fqdn` already exists."""
        fqdn = self.cleaned_data['fqdn']
        if Machine.objects.filter(fqdn__iexact=fqdn).count() == 0:
            self.add_error('fqdn', "FQDN does not exist!")
        return fqdn

    fqdn = forms.CharField(
        label='FQDN',
        max_length=200,
    )

    def get_order(self):
        """Return input order."""
        return [
            'fqdn',
        ]


class AnnotationAPIForm(forms.Form, BaseAPIForm):

    def __init__(self, *args, **kwargs):
        machine = kwargs.pop('machine', None)
        self.machine = machine

        super(AnnotationAPIForm, self).__init__(*args, **kwargs)

    text = forms.CharField(
        label='Text',
        max_length=1024,
    )

    def get_order(self):
        """Return input order."""
        return [
            'text',
        ]


class BMCAPIForm(forms.Form, BaseAPIForm):

    def __init__(self, *args, **kwargs):
        machine = kwargs.pop('machine', None)
        self.machine = machine

        super(BMCAPIForm, self).__init__(*args, **kwargs)

    username = forms.CharField(
        label='BMC Username',
        max_length=256,
        required=False
    )
    password = forms.CharField(
        label='BMC Password',
        max_length=256,
        required=False
    )
    fqdn = forms.CharField(
        label='FQDN',
        max_length=256,
    )
    mac = forms.CharField(
        label='MAC Address',
        max_length=256,
    )
    fence_name = forms.ChoiceField(
        choices=get_remote_power_type_choices('BMC'),
        label="Fence Agent",
    )

    def get_order(self):
        """Return input order."""
        return [
            'fqdn',
            'mac',
            'username',
            'password',
            'fence_name'
        ]


class RemotePowerAPIForm(forms.Form, BaseAPIForm):

    def __init__(self, *args, **kwargs):
        machine = kwargs.pop('machine', None)
        self.machine = machine

        super(RemotePowerAPIForm, self).__init__(*args, **kwargs)

        self._query_fields = (
            'fence_name',
            'remote_power_device',
            'port',
            'comment',
        )

        RemotePowerFormSet = inlineformset_factory(
            Machine,
            RemotePower,
            fields=self._query_fields,
            fk_name='machine'
        )
        formset = RemotePowerFormSet(instance=machine)

        self.fields = formset.form().fields
        self.fields['remote_power_device'].empty_label = 'None'
        self.fields['fence_name'].required = False

    def clean(self):
        """Add the machine to cleaned data for further processing."""
        cleaned_data = super(RemotePowerAPIForm, self).clean()
        cleaned_data['machine'] = self.machine
        remotepower = RemotePower(**cleaned_data)
        remotepower.clean()
        return cleaned_data

    def get_order(self):
        """Return input order."""
        return self._query_fields


class RemotePowerDeviceAPIForm(forms.Form, BaseAPIForm):
    fqdn = forms.CharField(label='FQDN', max_length=256)
    mac = forms.CharField(label='MAC', max_length=17)
    username = forms.CharField(label='Username', max_length=256, required=False)
    password = forms.CharField(label='Password', max_length=256, required=False)
    fence_name = forms.ChoiceField(
        choices=get_remote_power_type_choices("rpower_device"),
        label="Fence Agent"
    )

    def get_order(self):
        return ['fqdn', 'mac', 'fence_name', 'username', 'password']


class DeleteRemotePowerAPIForm(forms.Form, BaseAPIForm):

    def clean_fqdn(self):
        """Check whether `fqdn` already exists."""
        fqdn = self.cleaned_data['fqdn']
        if Machine.objects.filter(fqdn__iexact=fqdn).count() == 0:
            self.add_error('fqdn', "FQDN does not exist!")
        return fqdn

    fqdn = forms.CharField(
        label='FQDN',
        max_length=200,
    )

    def get_order(self):
        """Return input order."""
        return [
            'fqdn',
        ]
