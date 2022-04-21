import collections
import datetime
import logging

from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.formats import date_format

from orthos2.data.models import (Installation, Machine, Platform,
                                 ServerConfig, System, Vendor)

logger = logging.getLogger('views')


class NewUserForm(forms.Form):
    login = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        max_length=32,
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password2 = forms.CharField(
        label='Password confirmation',
        max_length=32,
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        max_length=64,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    def clean(self):
        cleaned_data = super(NewUserForm, self).clean()
        login = cleaned_data.get('login')
        password = cleaned_data.get('password')
        password2 = cleaned_data.get('password2')
        email = cleaned_data.get('email')

        if User.objects.filter(username=login).count() > 0:
            self.add_error('login', "User '{}' does already exist.".format(login))

        if len(password) < 8:
            self.add_error(
                'password',
                "Password is too short. It must contain at least 8 characters."
            )

        if password != password2:
            self.add_error('password', "Password and confirmation password do not match.")

        if email:
            valid_domains = ServerConfig.objects.list_by_key('mail.validdomains')

            if valid_domains is None:
                self.add_error(
                    None,
                    "Please contact support ({}).".format(settings.SUPPORT_CONTACT)
                )
            elif valid_domains and (email.split('@')[1] not in valid_domains):
                self.add_error(
                    'email',
                    "Please use a valid email domain: {}".format(', '.join(valid_domains))
                )

            if User.objects.filter(email__icontains=email).count():
                self.add_error('email', "Email address '{}' is already in use.".format(email))


class ReserveMachineForm(forms.Form):

    def __init__(self, *args, **kwargs):
        reason = kwargs.pop('reason', None)
        until = kwargs.pop('until', None)
        username = kwargs.pop('username', None)
        super(ReserveMachineForm, self).__init__(*args, **kwargs)
        self.fields['reason'].initial = reason
        if until is not None:
            self.fields['until'].initial = date_format(until, format=settings.SHORT_DATE_FORMAT)
        self.fields['username'].initial = username

    reason = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control'}),
        help_text='Please provide a reason why you reserve this machine.'
    )

    until = forms.DateField(
        widget=forms.TextInput(attrs={'id': 'datepicker', 'size': '10', 'class': 'form-control'}),
        help_text="Format: YYYY-MM-DD (TZ: " + timezone.get_default_timezone_name() +
                  "). Type '9999-12-31' for infinite reservation (superusers only)."
    )

    username = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )

    def clean(self):
        cleaned_data = super(ReserveMachineForm, self).clean()
        reserved_until = cleaned_data.get('until')

        if not reserved_until:
            # return due to further checks which needs datetime object
            return

        if reserved_until == datetime.date.max:
            pass

        elif reserved_until <= datetime.datetime.now().date():
            self.add_error('until', "Reservation date must be in the future (min. 1 day).")

        elif reserved_until > (datetime.datetime.now().date() + datetime.timedelta(days=90)):
            self.add_error('until', "Reservation period is limited (max. 90 days).")


class SearchForm(forms.Form):

    def clean(self):
        cleaned_data = super(SearchForm, self).clean()

        empty = True
        values = [value for key, value in cleaned_data.items() if not key.endswith('__operator')]
        for value in values:
            if value:
                empty = False

        if empty:
            self.add_error(None, "Please provide at least one search parameter.")

        if cleaned_data['ram_amount']:
            try:
                int(cleaned_data['ram_amount'])
            except ValueError:
                self.add_error('ram_amount', "Value must be a number.")

        if cleaned_data['cpu_cores']:
            try:
                int(cleaned_data['cpu_cores'])
            except ValueError:
                self.add_error('cpu_cores', "Value must be a number.")

    def get_vendors():
        vendors = [('', '--all--')]
        for vendor in Vendor.objects.all().values('id', 'name'):
            vendors.append((vendor['id'], vendor['name']))
        return vendors

    def get_platforms():
        platforms = [('', '--all--')]
        groups = {}
        for platform in Platform.objects.all():
            id = platform.id
            name = platform.name
            vendor = platform.vendor

            if platform.is_cartridge:
                continue

            if vendor.name in groups.keys():
                groups[vendor.name] += ((id, name),)
            else:
                groups[vendor.name] = ((id, name),)

        for vendor, platforms_ in groups.items():
            platforms.append((vendor, platforms_))
        return platforms

    def get_cartridge_platforms():
        platforms = [('', '--all--')]
        groups = {}
        for platform in Platform.objects.all():
            id = platform.id
            name = platform.name
            vendor = platform.vendor

            if not platform.is_cartridge:
                continue

            if vendor.name in groups.keys():
                groups[vendor.name] += ((id, name),)
            else:
                groups[vendor.name] = ((id, name),)

        for vendor, platforms_ in groups.items():
            platforms.append((vendor, platforms_))
        return platforms

    def get_distributions():
        installations = [('', '--all--')]
        for installation in Installation.objects.all().values('distribution').distinct():
            installations.append((installation['distribution'], installation['distribution']))
        return installations

    def get_systems():
        """Return system choices."""
        return Machine._meta.get_field('system').get_choices(blank_choice=[('', '--all--')])

    def get_architectures():
        """Return architecture choices."""
        return Machine._meta.get_field('architecture').get_choices(blank_choice=[('', '--all--')])

    enclosure__platform__vendor = forms.ChoiceField(
        required=False,
        choices=(get_vendors),
        widget=forms.Select(attrs={'class': 'custom-select form-control'}),
    )

    enclosure__platform = forms.ChoiceField(
        required=False,
        choices=(get_platforms),
        widget=forms.Select(attrs={'class': 'custom-select form-control'}),
    )

    platform = forms.ChoiceField(
        required=False,
        choices=(get_cartridge_platforms),
        widget=forms.Select(attrs={'class': 'custom-select form-control'}),
    )

    system = forms.ChoiceField(
        required=False,
        choices=(get_systems),
        widget=forms.Select(attrs={'class': 'custom-select form-control'}),
    )

    architecture = forms.ChoiceField(
        required=False,
        choices=(get_architectures),
        widget=forms.Select(attrs={'class': 'custom-select form-control'}),
    )

    fqdn = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    fqdn__operator = forms.CharField(
        initial='__icontains',
        widget=forms.HiddenInput()
    )

    cpu_model = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    cpu_model__operator = forms.CharField(
        initial='__icontains',
        widget=forms.HiddenInput()
    )

    cpu_flags = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    cpu_flags__operator = forms.CharField(
        initial='__icontains',
        widget=forms.HiddenInput()
    )

    ram_amount = forms.DecimalField(
        required=False,
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    ram_amount__operator = forms.ChoiceField(
        choices=(
            ('__gt', '>'),
            ('__exact', '='),
            ('__lt', '<')
        ),
        required=False,
        initial='__gt',
        widget=forms.RadioSelect(attrs={'autocomplete': 'off'})
    )

    cpu_cores = forms.DecimalField(
        required=False,
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    cpu_cores__operator = forms.ChoiceField(
        choices=(
            ('__gt', '>'),
            ('__exact', '='),
            ('__lt', '<')
        ),
        required=False,
        initial='__gt',
        widget=forms.RadioSelect(attrs={'autocomplete': 'off'})
    )

    hwinfo = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    hwinfo__operator = forms.CharField(
        initial='__icontains',
        widget=forms.HiddenInput()
    )

    dmidecode = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    dmidecode__operator = forms.CharField(
        initial='__icontains',
        widget=forms.HiddenInput()
    )

    dmesg = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    dmesg__operator = forms.CharField(
        initial='__icontains',
        widget=forms.HiddenInput()
    )

    lspci = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    lspci__operator = forms.CharField(
        initial='__icontains',
        widget=forms.HiddenInput()
    )

    lsmod = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    lsmod__operator = forms.CharField(
        initial='__icontains',
        widget=forms.HiddenInput()
    )

    installations__distribution = forms.ChoiceField(
        required=False,
        choices=(get_distributions),
        widget=forms.Select(attrs={'class': 'custom-select form-control'}),
    )

    reserved_by = forms.ChoiceField(
        required=False,
        choices=(
            ('__False', 'yes'),
            ('__True', 'no'),
            ('', 'not relevant')
        ),
        widget=forms.RadioSelect(attrs={'autocomplete': 'off'})
    )
    reserved_by__operator = forms.CharField(
        initial='__isnull',
        widget=forms.HiddenInput()
    )

    ipmi = forms.ChoiceField(
        required=False,
        choices=(
            ('__True', 'yes'),
            ('__False', 'no'),
            ('', 'not relevant')
        ),
        widget=forms.RadioSelect(attrs={'autocomplete': 'off'})
    )

    efi = forms.ChoiceField(
        required=False,
        choices=(
            ('__True', 'yes'),
            ('__False', 'no'),
            ('', 'not relevant')
        ),
        widget=forms.RadioSelect(attrs={'autocomplete': 'off'})
    )

    networkinterfaces__mac_address = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    networkinterfaces__mac_address__operator = forms.CharField(
        initial='__icontains',
        widget=forms.HiddenInput()
    )

    serialconsole = forms.ChoiceField(
        required=False,
        choices=(
            ('__False', 'yes'),
            ('__True', 'no'),
            ('', 'not relevant')
        ),
        widget=forms.RadioSelect(attrs={'autocomplete': 'off'})
    )
    serialconsole__operator = forms.CharField(
        initial='__isnull',
        widget=forms.HiddenInput()
    )

    remotepower = forms.ChoiceField(
        required=False,
        choices=(
            ('__False', 'yes'),
            ('__True', 'no'),
            ('', 'not relevant')
        ),
        widget=forms.RadioSelect(attrs={'autocomplete': 'off'})
    )
    remotepower__operator = forms.CharField(
        initial='__isnull',
        widget=forms.HiddenInput()
    )

    status_ipv4 = forms.ChoiceField(
        required=False,
        choices=Machine._meta.get_field('status_ipv4').get_choices(
            blank_choice=[('', 'Not relevant')]
        ),
        widget=forms.Select(attrs={'class': 'custom-select form-control'}),
    )

    status_ipv6 = forms.ChoiceField(
        required=False,
        choices=Machine._meta.get_field('status_ipv6').get_choices(
            blank_choice=[('', 'Not relevant')]
        ),
        widget=forms.Select(attrs={'class': 'custom-select form-control'}),
    )

    status_ssh = forms.ChoiceField(
        required=False,
        choices=(
            ('__True', 'yes'),
            ('__False', 'no'),
            ('', 'not relevant')
        ),
        widget=forms.RadioSelect(attrs={'autocomplete': 'off'})
    )

    status_login = forms.ChoiceField(
        required=False,
        choices=(
            ('__True', 'yes'),
            ('__False', 'no'),
            ('', 'not relevant')
        ),
        widget=forms.RadioSelect(attrs={'autocomplete': 'off'})
    )


class PasswordRestoreForm(forms.Form):

    def __init__(self, *args, **kwargs):
        username = kwargs.pop('username', None)

        super(PasswordRestoreForm, self).__init__(*args, **kwargs)

        if username is not None:
            self.fields['login'].initial = username

    login = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    email = forms.EmailField(
        max_length=64,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )


class PreferencesForm(forms.Form):

    def clean(self):
        cleaned_data = super(PreferencesForm, self).clean()
        new_password = cleaned_data.get('new_password')
        new_password2 = cleaned_data.get('new_password2')

        if len(new_password) < 8:
            self.add_error(
                'new_password',
                "Password is too short. It must contain at least 8 characters."
            )

        if new_password != new_password2:
            self.add_error('new_password', "Password and confirmation password do not match.")

    old_password = forms.CharField(
        max_length=32,
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    new_password = forms.CharField(
        max_length=32,
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    new_password2 = forms.CharField(
        label='Password confirmation',
        max_length=32,
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )


class SetupMachineForm(forms.Form):

    def __init__(self, *args, **kwargs):
        machine = kwargs.pop('machine', None)
        domain = machine.fqdn_domain

        architecture = machine.architecture.name
        '''
        Change choice html field here (domain.get_setup_records(..., grouped=True)
        grouped=True
           SLE-12-SP4-Server-LATEST
               install
               install-auto
               install-auto-ssh
           SLE-12-SP5-Server-LATEST
               install
               install-auto
               ...

        grouped=False
           SLE-12-SP4-Server-LATEST:install
           SLE-12-SP4-Server-LATEST:install-auto
           SLE-12-SP4-Server-LATEST:install-auto-ssh
           SLE-12-SP5-Server-LATEST:install
           SLE-12-SP5-Server-LATEST:install-auto
           ...
        '''
        records = domain.get_setup_records(architecture, grouped=True)
        logger.debug("Setup choices for %s.%s [%s]:\n%s\n", machine, domain, architecture, records)

        super(SetupMachineForm, self).__init__(*args, **kwargs)

        self.fields['setup'].choices = self.get_setup_select_choices(records)
        logger.debug("Setup choicen for %s.%s [%s]:\n%s\n",
                     machine, domain, architecture, self.fields['setup'].choices)

    def get_setup_select_choices(self, records):
        setup_records = []
        groups = collections.OrderedDict()

        if isinstance(records, list):
            for record in records:
                setup_records.append((record, record))

        elif isinstance(records, collections.OrderedDict):
            for distribution, record_group in records.items():

                for record in record_group:
                    option = record
                    value = distribution + ":" + record
                    if distribution not in groups.keys():
                        groups[distribution] = ((value, option),)
                    else:
                        groups[distribution] += ((value, option),)

            for distribution, record_group in groups.items():
                setup_records.append((distribution, record_group))

        if not setup_records:
            setup_records.append((None, 'no setup records available'))

        return setup_records

    setup = forms.ChoiceField(
        required=True,
        choices=[],
        widget=forms.Select(attrs={'class': 'custom-select form-control'})
    )


class VirtualMachineForm(forms.Form):

    def __init__(self, *args, **kwargs):
        virtualization_api = kwargs.pop('virtualization_api', None)

        super(VirtualMachineForm, self).__init__(*args, **kwargs)

        self.fields['system'].choices = [
            (system.pk, system.name) for system in System.objects.filter(
                virtual=True,
                name="KVM"
            )
        ]
        architectures, image_list = virtualization_api.get_image_list()
        self.fields['architecture'].choices = [(architectures[0], architectures[0])]
        self.fields['image'].choices = [('none', 'None')] + image_list

    def clean(self):
        """Set `image` to None; cast `decimal.Decimal()` to `int`."""
        cleaned_data = super(VirtualMachineForm, self).clean()

        if cleaned_data['image'] == 'none':
            cleaned_data['image'] = None

        cleaned_data['networkinterfaces'] = int(cleaned_data['networkinterfaces'])
        cleaned_data['ram_amount'] = int(cleaned_data['ram_amount'])
        cleaned_data['disk_size'] = int(cleaned_data['disk_size'])

        return cleaned_data

    uefi_boot = forms.BooleanField(
        label='Use UEFI boot',
        required=False,
        initial=False
    )

    ram_amount = forms.DecimalField(
        label='Memory (MB)',
        required=True,
        initial=2048,
        max_value=16384,
        min_value=512,
        help_text='Value between 512MB and 16384MB.',
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    image = forms.ChoiceField(
        required=True,
        choices=[],
        widget=forms.Select(attrs={'class': 'custom-select form-control'})
    )

    networkinterfaces = forms.DecimalField(
        required=True,
        initial=1,
        max_value=5,
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    parameters = forms.CharField(
        required=False,
        help_text="e.g. '--cdrom /dev/cdrom'",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    system = forms.ChoiceField(
        required=True,
        choices=[],
        widget=forms.Select(attrs={'class': 'custom-select form-control'}),
        initial=0
    )

    architecture = forms.ChoiceField(
        required=True,
        choices=[],
        widget=forms.Select(attrs={'class': 'custom-select form-control'}),
        initial=0
    )

    disk_size = forms.DecimalField(
        label='Disk size (GB)',
        required=True,
        initial=30,
        max_value=100,
        min_value=10,
        help_text='Value between 10GB and 100GB; applies only if no image is selected.',
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    vnc = forms.BooleanField(
        label='Enable VNC',
        required=False,
        initial=False
    )
