from django import forms
from django.conf.urls import re_path
from django.contrib import admin, messages
from django.contrib.admin.templatetags.admin_list import _boolean_icon
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from orthos2.utils.misc import DHCPRecordOption

from .models import (Annotation, Architecture, BMC, Domain, Enclosure, Installation,
                     Machine, MachineGroup, MachineGroupMembership,
                     NetworkInterface, Platform, RemotePower, RemotePowerDevice,
                     SerialConsole, SerialConsoleType, ServerConfig, System, Vendor,
                     VirtualizationAPI, is_unique_mac_address, validate_dns,
                     validate_mac_address)


class BMCInline(admin.StackedInline):
    model = BMC
    extra = 1

    def get_formset(self, request, obj=None, **kwargs):
        """Set machine object for `formfield_for_foreignkey` method."""
        self.machine = obj
        return super(BMCInline, self).get_formset(request, obj, **kwargs)


class SerialConsoleInline(admin.StackedInline):
    model = SerialConsole
    extra = 0
    fk_name = 'machine'
    verbose_name = 'Serial Console'
    verbose_name_plural = 'Serial Console'
    fields = (
        'type',
        'cscreen_server',
        'baud_rate',
        'kernel_device',
        'management_bmc',
        'console_server',
        'device',
        'port',
        'command',
        'comment'
    )

#    def formfield_for_foreignkey(self, db_field, request, **kwargs):
#        """Do only show management BMC belonging to the machine itself."""
#        if self.machine and db_field.name == 'management_bmc':
#            if hasattr(self.machine, 'bmc'):
#                kwargs['queryset'] = (self.machine.bmc)
#            else:
#                kwargs['queryset'] = set()
#        return super(SerialConsoleInline, self).formfield_for_foreignkey(
#            db_field,
#            request,
#            **kwargs
#        )
#
    def get_formset(self, request, obj=None, **kwargs):
        """Set machine object for `formfield_for_foreignkey` method."""
        self.machine = obj
        return super(SerialConsoleInline, self).get_formset(request, obj, **kwargs)


class RemotePowerInlineRpower(admin.StackedInline):
    model = RemotePower
    extra = 0
    fk_name = 'machine'
    verbose_name = 'Remote Power'
    verbose_name_plural = 'Remote Power'
    fields = ["port", "remote_power_device", "options"]

    def get_formset(self, request, obj=None, **kwargs):
        """Set machine object for `formfield_for_foreignkey` method."""
        self.machine = obj
        return super(RemotePowerInlineRpower, self).get_formset(request, obj, **kwargs)


class RemotePowerInlineBMC(admin.StackedInline):
    model = RemotePower
    extra = 0
    fk_name = 'machine'
    verbose_name = 'Remote Power'
    verbose_name_plural = 'Remote Power'
    fields = ["options"]

    def get_formset(self, request, obj=None, **kwargs):
        """Set machine object for `formfield_for_foreignkey` method."""
        self.machine = obj
        return super(RemotePowerInlineBMC, self).get_formset(request, obj, **kwargs)


class RemotePowerInlineHypervisor(admin.StackedInline):
    model = RemotePower
    extra = 0
    fk_name = 'machine'
    verbose_name = 'Remote Power'
    verbose_name_plural = 'Remote Power'
    fields = ["fence_name", "options"]

    def get_formset(self, request, obj=None, **kwargs):
        """Set machine object for `formfield_for_foreignkey` method."""
        self.machine = obj
        return super(RemotePowerInlineHypervisor, self).get_formset(request, obj, **kwargs)


class NetworkInterfaceInline(admin.TabularInline):
    model = NetworkInterface
    extra = 0
    fk_name = 'machine'
    readonly_fields = (
        'primary',
        'mac_address',
        'name',
        'ethernet_type',
        'driver_module'
    )

    def has_add_permission(self, request, obj=None):
        """Network interfaces get added by machine scan."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Network interfaces get deleted by machine scan."""
        return False


class AnnotationInline(admin.TabularInline):
    model = Annotation
    extra = 0
    fk_name = 'machine'
    readonly_fields = (
        'text',
        'reporter',
        'created'
    )

    def has_add_permission(self, request, obj=None):
        """Annotations are added at machine detail view."""
        return False


class MachineAdminForm(forms.ModelForm):

    mac_address = forms.CharField(
        label='MAC address',
        validators=[validate_mac_address]
    )

    class Meta:
        model = Machine
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        """Set primary MAC address and virtualization API type in the form fields."""
        instance = kwargs.get('instance', None)

        if instance:
            if isinstance(instance.virtualization_api, VirtualizationAPI):
                instance.virtualization_api = instance.virtualization_api.get_type()

        super(MachineAdminForm, self).__init__(*args, **kwargs)

        if instance:
            self.fields['mac_address'].initial = instance.mac_address

            self.machine = instance

    def save(self, commit=True):
        machine = super(MachineAdminForm, self).save(commit=False)
        machine.mac_address = self.cleaned_data['mac_address']
        if commit:
            machine.save()
        return machine

    def clean_mac_address(self):
        """Check if another machine has already this MAC address."""
        mac_address = self.cleaned_data['mac_address']

        if hasattr(self, 'machine'):
            exclude = self.machine.networkinterfaces.all().values_list('mac_address', flat=True)
        else:
            exclude = []

        if not is_unique_mac_address(mac_address, exclude=exclude):
            raise ValidationError(
                "MAC address '{}' is already used by '{}'!".format(
                    mac_address,
                    NetworkInterface.objects.get(mac_address=mac_address).machine.fqdn
                )
            )

        return mac_address

    def clean_fqdn(self):
        """Check if another machine has already this FQDN (except self)."""
        fqdn = self.cleaned_data['fqdn']

        if hasattr(self, 'machine'):
            if Machine.objects.filter(fqdn=fqdn).exclude(pk=self.machine.pk):
                raise ValidationError("FQDN is already in use!")
        else:
            # new machine
            if Machine.objects.filter(fqdn=fqdn):
                raise ValidationError("FQDN is already in use!")
        return fqdn

    def clean_use_bmc(self):
        use_bmc = self.cleaned_data['use_bmc']
        system = self.cleaned_data['system']
        if system.virtual and use_bmc:
            raise ValidationError("System {} is virtual. Virtual machines can't have a BMC"
                                  .format(system))
        return use_bmc

    def clean_hypervisor(self):
        hypervisor = self.cleaned_data['hypervisor']
        system = self.cleaned_data['system']
        if hypervisor and not system.virtual:
            raise ValidationError("system {} is not virtual. Only Virtual Machines may have "
                                  "a hypervisor".format(system))
        if hypervisor and hypervisor.is_virtual_machine():
            raise ValidationError("{} is a Virtual Machines. Hypervisors must be physical")
        return hypervisor

    def clean(self):
        """
        Only collect system information if connectivity is set to `Full`.
        """
        cleaned_data = self.cleaned_data

        check_connectivity = cleaned_data['check_connectivity']
        collect_system_information = cleaned_data['collect_system_information']

        if collect_system_information and check_connectivity != Machine.Connectivity.ALL:
            self.add_error(
                'collect_system_information',
                "Connectivity check must set to 'Full'!"
            )

        return cleaned_data


class MachineArchitectureFilter(admin.SimpleListFilter):
    title = 'Architecture'

    parameter_name = 'arch'

    def lookups(self, request, model_admin):
        architectures = Architecture.objects.all()
        result = []

        for architecture in architectures:
            result.append((architecture.id, _(architecture.name)))

        return result

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(architecture_id=self.value())


class MachineSystemFilter(admin.SimpleListFilter):
    title = 'System'

    parameter_name = 'system'

    def lookups(self, request, model_admin):
        systems = System.objects.all()
        result = []

        result.append(('administrative', _('Administrative')))
        result.append(('inactive', _('Inactive')))

        for system in systems:
            result.append((system.id, _(system.name)))

        return result

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            if value == 'administrative':
                return queryset.filter(Q(administrative=True) | Q(system__administrative=True))
            elif value == 'inactive':
                return queryset.filter(Q(active=False))
            else:
                return queryset.filter(system_id=self.value())


class MachineDomainFilter(admin.SimpleListFilter):
    title = 'Domain'

    parameter_name = 'domain'

    def lookups(self, request, model_admin):
        domains = Domain.objects.all()
        result = []

        for domain in domains:
            result.append((domain.id, _(domain.name)))

        return result

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(fqdn_domain_id=self.value())


class MachineGroupFilter(admin.SimpleListFilter):
    title = 'Machine Groups'

    parameter_name = 'machinegroup'

    def lookups(self, request, model_admin):
        machinegroups = MachineGroup.objects.all()
        result = []

        for group in machinegroups:
            result.append((group.id, _(group.name)))

        return result

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(group_id=self.value())


class MachineAdmin(admin.ModelAdmin):
    form = MachineAdminForm

    list_display = (
        'fqdn',
        'enclosure',
        'architecture',
        'system',
        'group',
        'write_dhcpv4',
        'write_dhcpv6',
        'active'
    )
    list_per_page = 50
    search_fields = ('fqdn',)
    list_filter = (
        MachineArchitectureFilter,
        MachineSystemFilter,
        MachineDomainFilter,
        MachineGroupFilter,
    )
    fieldsets = (
        (None, {
            'fields': (
                (
                    'fqdn',
                    'enclosure'
                ),
                'mac_address',
                'architecture',
                'system',
                'group',
                (
                    'serial_number',
                    'product_code'
                ),
                'comment',
                'platform',
                'contact_email',
                'kernel_options',
            ),
        }),
        ('PROPERTIES', {
            'fields': (
                (
                    'administrative',
                    'nda'
                ),
                'active',
                'use_bmc'
            )
        }),
        ('VIRTUALIZATION', {
            'fields': (
                (
                    'vm_dedicated_host',
                    'vm_auto_delete'
                ),
                'vm_max',
                'virtualization_api',
                'hypervisor'
            ),
        }),
        ('MACHINE CHECKS', {
            'fields': (
                'check_connectivity',
                (
                    'collect_system_information'
                )
            )
        }),
        ('DHCP', {
            'fields': (
                'dhcpv4_write',
                'dhcpv6_write',
                'dhcp_filename'
            ),
        })
    )

    def write_dhcpv4(self, machine):
        """
        Show whether an DHCPv4 record is being written.

        The hierarchy is:
            Machine > [Group >] Architecture

        If a machine is in a machine group, the machine group setting decides whether to write a
        DHCP group file (e.g. 'group_foo.conf').

        If a machine is not in a machine group, the respective machine architecture decides whether
        to write an architecture DHCP file (e.g. 'x86_64.conf').

        If so, the machine setting decides whether the entry exists, does not exist or DHCP
        requests are ignored for this machine.
        """
        from django.contrib.admin.templatetags.admin_list import _boolean_icon

        reasons_disabled = []

        if machine.group:
            if not machine.group.dhcpv4_write:
                reasons_disabled.append('excluded by group')

        elif not machine.architecture.dhcpv4_write:
            reasons_disabled.append('excluded by architecture')

        if machine.dhcpv4_write == DHCPRecordOption.EXCLUDE:
            reasons_disabled.append('excluded by machine')

        elif machine.dhcpv4_write == DHCPRecordOption.IGNORE:
            reasons_disabled.append('ignore machine')

        if not reasons_disabled:
            return _boolean_icon(True)

        return '{} <span class="help">({})</span>'.format(
            _boolean_icon(False),
            ', '.join(reasons_disabled)
        )
    write_dhcpv4.allow_tags = True

    def write_dhcpv6(self, machine):
        """
        Show whether an DHCPv6 record is being written. The hierarchy is:

        Machine > [Group >] Architecture

        If a machine is in a machine group, the machine group setting decides whether to write a
        DHCP group file (e.g. 'group_foo.conf').

        If a machine is not in a machine group, the respective machine architecture decides whether
        to write an architecture DHCP file (e.g. 'x86_64.conf').

        If so, the machine setting decides whether the entry exists, does not exist or DHCP
        requests are ignored for this machine.
        """
        from django.contrib.admin.templatetags.admin_list import _boolean_icon

        reasons_disabled = []

        if machine.group:
            if not machine.group.dhcpv6_write:
                reasons_disabled.append('excluded by group')

        elif not machine.architecture.dhcpv6_write:
            reasons_disabled.append('excluded by architecture')

        if machine.dhcpv6_write == DHCPRecordOption.EXCLUDE:
            reasons_disabled.append('excluded by machine')

        elif machine.dhcpv6_write == DHCPRecordOption.IGNORE:
            reasons_disabled.append('ignore machine')

        if not reasons_disabled:
            return _boolean_icon(True)

        return '{} <span class="help">({})</span>'.format(
            _boolean_icon(False),
            ', '.join(reasons_disabled)
        )
    write_dhcpv6.allow_tags = True

    def get_queryset(self, request):
        """
        Filter machine list. A superuser is authorized to see/edit all machines. If a user is
        authorized to change machine models and is privileged in any machine group, then all
        machines belonging to the respective machine group(s) get listed.
        """
        queryset = super(MachineAdmin, self).get_queryset(request)
        user = request.user

        if user.is_superuser:
            return queryset

        query = None

        for membership in user.memberships.all():
            if membership.is_privileged:
                if query:
                    query = query | Q(group_id=membership.group_id)
                else:
                    query = Q(group_id=membership.group_id)

        if query:
            queryset = queryset.filter(query)
        else:
            queryset = Machine.objects.none()

        return queryset

    def add_view(self, request, form_url='', extra_context=None):
        """
        Return view for 'Add machine' and do not show inlines. This is due the fact that these
        objects need a related machine object (which doesn't exist yet) for several checks.
        """
        self.inlines = ()
        return super(MachineAdmin, self).add_view(request, form_url, extra_context)

    def get_fieldsets(self, request, machine):
        """Do not show 'VIRTUALIZATION' fieldset for administrative systems."""
        fieldsets = super(MachineAdmin, self).get_fieldsets(request)

        if machine and machine.system.administrative:
            fieldsets_ = ()

            for fieldset in fieldsets:
                if fieldset[0] != 'VIRTUALIZATION':
                    fieldsets_ += (fieldset,)

            fieldsets = fieldsets_

        return fieldsets

    def change_view(self, request, object_id, form_url='', extra_context=None):
        """Return changes view with inlines for non-administrative systems."""
        machine = Machine.objects.get(pk=object_id)

        if not self.get_object(request, object_id):
            messages.add_message(
                request,
                messages.ERROR,
                'You are not allowed to edit this machine!',
                extra_tags='error'
            )

        if machine.system.administrative:
            self.inlines = (NetworkInterfaceInline, BMCInline)
        else:
            if machine.use_bmc:
                if hasattr(machine, 'bmc'):
                    self.inlines = (
                        RemotePowerInlineBMC,
                        NetworkInterfaceInline,
                        AnnotationInline,
                        BMCInline
                    )
                else:
                    self.inlines = (
                        NetworkInterfaceInline,
                        AnnotationInline,
                        BMCInline
                    )
            elif machine.is_virtual_machine():
                self.inlines = (
                        RemotePowerInlineHypervisor,
                        NetworkInterfaceInline,
                        AnnotationInline
                    )
            else:
                self.inlines = (
                        RemotePowerInlineRpower,
                        NetworkInterfaceInline,
                        AnnotationInline
                    )

        return super(MachineAdmin, self).change_view(request, object_id, form_url, extra_context)

    def save_formset(self, request, form, formset, change):
        formset.save()
        machine = form.save(commit=False)
        if machine.use_bmc and hasattr(machine, 'bmc') and not hasattr(machine, 'remotepower'):
            machine.remotepower = RemotePower(machine.bmc.fence_name, machine, machine.bmc)
            machine.bmc.save()
            machine.remotepower.save()
            machine.save()


admin.site.register(Machine, MachineAdmin)


class DomainAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'cobbler_server_list',
        'tftp_server',
        'get_machine_count',
        'setup_support'
    )
    # enables nifty unobtrusive JavaScript “filter” interface
    filter_horizontal = (
        'cobbler_server',
        'setup_architectures',
        'setup_machinegroups'
    )

    def setup_support(self, obj):
        """Return list of setup supported architectures/machine groups as string."""
        architectures = 'Architectures: '
        machinegroups = 'Machine Groups: '
        link_pattern = '<a href="{}" class="text-muted">{}</a>, '

        if obj.setup_architectures.all().count() == 0:
            architectures += '-'
        else:
            for architecture in obj.setup_architectures.all():
                architectures += link_pattern.format(
                    reverse('admin:data_architecture_change', args=[architecture.pk]),
                    architecture.name
                )
            architectures = architectures.rstrip(' ,')

        if obj.setup_machinegroups.all().count() == 0:
            machinegroups += '-'
        else:
            for machinegroup in obj.setup_machinegroups.all():
                machinegroups += link_pattern.format(
                    reverse('admin:data_machinegroup_change', args=[machinegroup.pk]),
                    machinegroup.name
                )
            machinegroups = machinegroups.rstrip(' ,')

        return format_html('{}<br/>{}'.format(architectures, machinegroups))

    def cobbler_server_list(self, obj):
        """Return DHCP server list as string."""
        if obj.cobbler_server.all().count() == 0:
            return '-'
        return ', '.join([cobbler_server.fqdn for cobbler_server in obj.cobbler_server.all()])

    def delete_model(self, request, obj=None):
        try:
            obj.delete()
        except ValidationError as e:
            messages.error(request, e.message)

    def has_delete_permission(self, request, obj=None):
        if obj is not None and obj.machine_set.count() > 0:
            return False
        return super(DomainAdmin, self).has_delete_permission(request, obj=obj)


admin.site.register(Domain, DomainAdmin)


class EnclosureAdmin(admin.ModelAdmin):
    readonly_fields = (
        'location_room',
        'location_rack',
        'location_rack_position'
    )
    list_display = ('name', 'machine_count', 'platform_name')
    search_fields = ('name',)

    def machine_count(self, obj):
        """Return machine counter of enclosure."""
        return obj.machine_set.count()

    def platform_name(self, obj):
        """Return name of enclosures platform."""
        platform = obj.platform
        if platform:
            return platform.name
        return None


admin.site.register(Enclosure, EnclosureAdmin)


class RemotePowerDeviceAdmin(admin.ModelAdmin):
    list_display = ['fqdn']


admin.site.register(RemotePowerDevice, RemotePowerDeviceAdmin)


class ServerConfigAdmin(admin.ModelAdmin):
    list_display = ('key', 'augmented_value')
    search_fields = ('key', 'value')

    # https://medium.com/@hakibenita/how-to-add-custom-action-buttons-to-django-admin-8d266f5b0d41
    def get_urls(self):
        """Add customn URLs to server configuration admin view."""
        urls = super(ServerConfigAdmin, self).get_urls()
        custom_urls = [
            re_path(
                r'^(?P<serverconfig_id>.+)/switch/$',
                self.admin_site.admin_view(self.process_boolean_switch),
                name='boolean_switch'
            ),
        ]
        return custom_urls + urls

    def process_boolean_switch(self, request, serverconfig_id, *args, **kwargs):
        """Enable/disable value."""
        action = request.GET.get('action', None)

        if (action is not None) and (action in {'enable', 'disable'}):
            try:
                configuration = ServerConfig.objects.get(pk=serverconfig_id)

                if action == 'enable':
                    configuration.value = 'bool:true'
                elif action == 'disable':
                    configuration.value = 'bool:false'

                configuration.save()
                messages.info(request, "Successfully {}d: '{}'.".format(action, configuration.key))

            except Exception as e:
                messages.error(request, str(e), extra_tags='error')

        return redirect('admin:data_serverconfig_changelist')

    def augmented_value(self, obj):
        """Add buttons for boolean values ('bool:true' or 'bool:false')."""
        if obj.value.lower() == 'bool:false':
            button = _boolean_icon(False)
            button += ' <span class="help">(<a href="{}?action=enable">Enable</a>)</span>'
            return format_html(button, reverse('admin:boolean_switch', args=[obj.pk]))
        elif obj.value.lower() == 'bool:true':
            button = _boolean_icon(True)
            button += ' <span class="help">(<a href="{}?action=disable">Disable</a>)</span>'
            return format_html(button, reverse('admin:boolean_switch', args=[obj.pk]))

        return obj.value


admin.site.register(ServerConfig, ServerConfigAdmin)


class PlatformAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_vendor', 'get_enclosure_count', 'is_cartridge')
    list_per_page = 50
    search_fields = ('name',)


admin.site.register(Platform, PlatformAdmin)


class ArchitectureAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'get_machine_count',
        'dhcpv4_write',
        'dhcpv6_write',
        'dhcp_filename'
    )

    def delete_model(self, request, obj=None):
        try:
            obj.delete()
        except ValidationError as e:
            messages.error(request, e.message)

    def has_delete_permission(self, request, obj=None):
        if obj is not None and obj.machine_set.count() > 0:
            return False
        return super(ArchitectureAdmin, self).has_delete_permission(request, obj=obj)


admin.site.register(Architecture, ArchitectureAdmin)


class SerialConsoleTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'command')


admin.site.register(SerialConsoleType, SerialConsoleTypeAdmin)


class SystemAdmin(admin.ModelAdmin):
    list_display = ('name', 'virtual', 'administrative')


admin.site.register(System, SystemAdmin)


class MachineGroupMembershipInline(admin.TabularInline):
    model = MachineGroupMembership
    extra = 0


class MachinesInline(admin.TabularInline):
    model = Machine
    fields = ('fqdn',)
    readonly_fields = ('fqdn',)

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class MachineGroupAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'machines',
        'dhcpv4_write',
        'dhcpv6_write',
        'dhcp_filename'
    )
    inlines = (MachinesInline, MachineGroupMembershipInline)

    def machines(self, obj):
        machines = Machine.objects.filter(group=obj)
        output = ', '.join([machine.fqdn for machine in machines])
        return output


admin.site.register(MachineGroup, MachineGroupAdmin)
admin.site.register(Vendor)
