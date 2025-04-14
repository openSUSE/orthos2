import ipaddress
from typing import Any, Dict, List, Optional, Tuple, Union

from django import forms
from django.contrib import admin, messages
from django.contrib.admin import ModelAdmin
from django.contrib.admin.templatetags.admin_list import _boolean_icon  # type: ignore
from django.core.exceptions import ValidationError
from django.db.models import Q, QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import URLPattern, re_path, reverse
from django.utils.html import format_html

from orthos2.api.forms import RemotePowerDeviceAPIForm
from orthos2.data.models import (
    BMC,
    Annotation,
    Architecture,
    Domain,
    DomainAdmin,
    Enclosure,
    Machine,
    MachineGroup,
    MachineGroupMembership,
    NetworkInterface,
    Platform,
    RemotePower,
    RemotePowerDevice,
    SerialConsole,
    SerialConsoleType,
    ServerConfig,
    System,
    Vendor,
)
from orthos2.utils.misc import get_domain, is_unique_mac_address, suggest_host_ip
from orthos2.utils.remotepowertype import RemotePowerType


class BMCForm(forms.ModelForm):
    def clean(self):
        """
        Verify that all information inside a form is valid.
        """
        if not self.is_valid():
            return
        self.__verify_username_password()
        self.__suggest_ip_address()
        self.__verify_ip_in_network()

    def __verify_username_password(self) -> None:
        """
        Called during self.clean(). Verifies the username and password are both given.
        """
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")
        if username and not password:
            raise forms.ValidationError("Username also needs a password")
        if password and not username:
            raise forms.ValidationError("Password also needs a username")

    def __verify_ip_in_network(self) -> None:
        """
        Called during self.clean(). Verifies the given IP address is in the network of the FQDN.
        """
        bmc_machine = self.cleaned_data.get("machine")
        if bmc_machine is None:
            raise ValidationError("No machine for BMC found")
        if bmc_machine.administrative:
            # Exclude administrative machines from this check.
            return

        bmc_domain = Domain.objects.get(
            name=get_domain(self.cleaned_data.get("fqdn", ""))
        )
        bmc_network_v4 = ipaddress.ip_network(
            f"{bmc_domain.ip_v4}/{bmc_domain.subnet_mask_v4}"
        )
        bmc_network_v6 = ipaddress.ip_network(
            f"{bmc_domain.ip_v6}/{bmc_domain.subnet_mask_v6}"
        )

        ip_address_v4 = self.cleaned_data.get("ip_address_v4")
        ip_address_v6 = self.cleaned_data.get("ip_address_v6")
        if ip_address_v4 and ipaddress.ip_address(ip_address_v4) not in bmc_network_v4:
            raise ValidationError("IPv4 address is not in the chosen network!")
        if ip_address_v6 and ipaddress.ip_address(ip_address_v6) not in bmc_network_v6:
            raise ValidationError("IPv4 address is not in the chosen network!")

    def __suggest_ip_address(self) -> None:
        """
        Called during self.clean(). Suggests an IP address in case a MAC is present.
        """
        bmc_domain = Domain.objects.get(name=get_domain(self.cleaned_data["fqdn"]))
        interface_mac = self.cleaned_data.get(f"mac")
        if interface_mac == "":
            # We don't want to autogenerate an address for interfaces without MAC addresses
            self.cleaned_data["ip_address_v4"] = ""
            self.cleaned_data["ip_address_v6"] = ""
        else:
            ip_address_v4 = self.cleaned_data.get("ip_address_v4")
            if ip_address_v4 == "127.0.0.1":
                self.cleaned_data["ip_address_v4"] = suggest_host_ip(4, bmc_domain)
            ip_address_v6 = self.cleaned_data.get("ip_address_v6")
            if ip_address_v6 == "::1":
                self.cleaned_data["ip_address_v6"] = suggest_host_ip(6, bmc_domain)


class BMCFormInlineFormSet(forms.models.BaseInlineFormSet):
    def clean(self):
        if not self.is_valid():
            return
        self.__verify_unique_mac_address()
        self.__verify_unique_ip_address()

    def __verify_unique_mac_address(self):
        """
        This method is called in clean. It is verifying that all MAC addresses are unique inside the DB.
        """
        old_mac_addresses = list(
            self.instance.networkinterfaces.all().values_list("mac_address", flat=True)
        )
        if self.instance.has_bmc() and self.instance.bmc.mac != "":
            old_mac_addresses.append(self.instance.bmc.mac)

        for interface in self.cleaned_data:
            mac = interface.get("mac_address")
            if mac == "":
                continue
            if not is_unique_mac_address(mac, exclude=old_mac_addresses):
                raise ValidationError(f"MAC address {mac} is not unique")

    def __verify_unique_ip_address(self):
        """
        This method is called in clean. It is verifying if all IPs given are unique.
        """
        for interface in self.cleaned_data:
            ip_address_v4 = interface.get("ip_address_v4")
            ip_address_v6 = interface.get("ip_address_v6")
            if (
                NetworkInterface.objects.filter(ip_address_v4=ip_address_v4).count() > 1
                or BMC.objects.filter(ip_address_v4=ip_address_v4).count() > 1
            ):
                raise ValidationError(
                    "IPv4 address already in use, please choose another one!"
                )
            if (
                NetworkInterface.objects.filter(ip_address_v6=ip_address_v6).count() > 1
                or BMC.objects.filter(ip_address_v6=ip_address_v6).count() > 1
            ):
                raise ValidationError(
                    "IPv6 address already in use, please choose another one!"
                )


class BMCInline(admin.StackedInline):
    model = BMC
    extra = 0
    formset = BMCFormInlineFormSet
    form = BMCForm

    def get_formset(
        self, request: HttpRequest, obj: Optional["Machine"] = None, **kwargs: Any
    ):
        """Set machine object for `formfield_for_foreignkey` method."""
        self.machine = obj
        formset = super(BMCInline, self).get_formset(request, obj, **kwargs)
        return formset


class SerialConsoleInline(admin.StackedInline):
    model = SerialConsole
    extra = 0
    fk_name = "machine"
    verbose_name = "Serial Console"
    verbose_name_plural = "Serial Console"
    fields = (
        "stype",
        "baud_rate",
        "kernel_device",
        "kernel_device_num",
        "console_server",
        "port",
        "command",
        "comment",
        "rendered_command",
    )
    readonly_fields = ("rendered_command",)

    def get_formset(
        self, request: HttpRequest, obj: Optional["Machine"] = None, **kwargs: Any
    ):
        """Set machine object for `formfield_for_foreignkey` method."""
        self.machine = obj
        return super(SerialConsoleInline, self).get_formset(request, obj, **kwargs)


class RemotePowerInlineFormset(forms.models.BaseInlineFormSet):
    def clean(self) -> None:
        if not self.cleaned_data:
            return
        data = self.cleaned_data[0]
        port = data.get("port")
        dev = data.get("remote_power_device")
        machine = data.get("machine")
        # dev = RemotePowerDevice.get_by_str(remote_power_device)
        if not dev:
            raise forms.ValidationError("Bad remote device - Open a bug")
        fence = RemotePowerType.from_fence(dev.fence_name)
        if not fence:
            raise forms.ValidationError("Fence not found - Open a bug")
        if fence.use_port:
            if not port:
                raise forms.ValidationError(
                    "Fence {} needs a port number".format(fence.fence)
                )
            try:
                int(port)
            except ValueError:
                raise forms.ValidationError("{} - Port must be a number".format(port))
        elif fence.use_hostname_as_port:
            if machine is None:
                raise forms.ValidationError(
                    "Machine is required for remote power device!"
                )
            if not port:
                port = machine.hostname
            elif port != machine.hostname:
                raise forms.ValidationError(
                    "{} - Port must be empty or hostname for fence: {}".format(
                        port, dev.fence_name
                    )
                )
        else:
            if port:
                raise forms.ValidationError(
                    "Fence {} needs no port, please leave emtpy".format(fence.fence)
                )


class RemotePowerInlineRpower(admin.StackedInline):
    model = RemotePower
    formset = RemotePowerInlineFormset
    extra = 0
    fk_name = "machine"
    verbose_name = "Remote Power via PowerSwitch Device"
    verbose_name_plural = "Remote Power via PowerSwitch Device"
    fields = ["port", "remote_power_device", "options"]

    def get_formset(
        self, request: HttpRequest, obj: Optional["Machine"] = None, **kwargs: Any
    ):
        """Set machine object for `formfield_for_foreignkey` method."""
        self.machine = obj
        return super(RemotePowerInlineRpower, self).get_formset(request, obj, **kwargs)


class RemotePowerInlineBMC(admin.StackedInline):
    model = RemotePower
    extra = 0
    fk_name = "machine"
    verbose_name = "Remote Power via BMC"
    verbose_name_plural = "Remote Power via BMC"
    fields = ["options"]

    def get_formset(self, request, obj=None, **kwargs):
        """Set machine object for `formfield_for_foreignkey` method."""
        self.machine = obj
        return super(RemotePowerInlineBMC, self).get_formset(request, obj, **kwargs)


class RemotePowerInlineHypervisor(admin.StackedInline):
    model = RemotePower
    extra = 0
    fk_name = "machine"
    verbose_name = "Remote Power via Hypervisor"
    verbose_name_plural = "Remote Power via Hypervisor"
    fields = ["fence_name", "options"]

    def get_formset(self, request: HttpRequest, obj: Any = None, **kwargs: Any):
        """Set machine object for `formfield_for_foreignkey` method."""
        self.machine = obj
        return super(RemotePowerInlineHypervisor, self).get_formset(
            request, obj, **kwargs
        )


class NetworkInterfaceForm(forms.ModelForm):
    def clean(self):
        """
        Verifies that the data for a single network interface is valid.
        """
        if not self.is_valid():
            return
        self.__suggest_ip_address()
        self.__verify_ip_address_in_network()

    def __suggest_ip_address(self) -> None:
        """
        Called during self.__clean(). Suggests an IP address in case one is desired but not set.
        """
        interface_machine = self.cleaned_data.get("machine")
        if not interface_machine:
            raise forms.ValidationError("Cannot retrieve machine for interface!")
        machine_domain = Domain.objects.get(name=get_domain(interface_machine.fqdn))
        interface_mac = self.cleaned_data.get(f"mac_address")
        if interface_mac == "":
            # We don't want to autogenerate an address for interfaces without MAC addresses
            self.cleaned_data["ip_address_v4"] = ""
            self.cleaned_data["ip_address_v6"] = ""
        else:
            ip_address_v4 = self.cleaned_data.get("ip_address_v4")
            if ip_address_v4 == "127.0.0.1":
                self.cleaned_data["ip_address_v4"] = suggest_host_ip(4, machine_domain)
            ip_address_v6 = self.cleaned_data.get("ip_address_v6")
            if ip_address_v6 == "::1":
                self.cleaned_data["ip_address_v6"] = suggest_host_ip(6, machine_domain)

    def __verify_ip_address_in_network(self):
        """
        This method is called in clean. It is verifying that the chosen IP is inside the configured network.
        """
        interface_machine = self.cleaned_data.get("machine")
        if not interface_machine:
            raise forms.ValidationError("Cannot retrieve machine for interface!")
        if interface_machine.administrative:
            # Exclude administrative machines from this check
            return
        machine_domain = Domain.objects.get(name=get_domain(interface_machine.fqdn))
        machine_network_v4 = ipaddress.ip_network(
            f"{machine_domain.ip_v4}/{machine_domain.subnet_mask_v4}"
        )
        machine_network_v6 = ipaddress.ip_network(
            f"{machine_domain.ip_v6}/{machine_domain.subnet_mask_v6}"
        )

        ip_address_v4 = self.cleaned_data.get("ip_address_v4")
        ip_address_v6 = self.cleaned_data.get("ip_address_v6")
        if (
            ip_address_v4
            and ipaddress.ip_address(ip_address_v4) not in machine_network_v4
        ):
            raise ValidationError("IPv4 address is not in the chosen network!")
        if (
            ip_address_v6
            and ipaddress.ip_address(ip_address_v6) not in machine_network_v6
        ):
            raise ValidationError("IPv4 address is not in the chosen network!")


class NetworkInterfaceInlineFormset(forms.models.BaseInlineFormSet):
    def clean(self) -> None:
        """
        Verifies that the data for all network interfaces is valid if viewed at together.
        """
        if not self.is_valid():
            return
        self.__verify_single_primary_interface()
        self.__verify_unique_mac_address()
        self.__verify_unique_ip_address()

    def __verify_single_primary_interface(self):
        """
        This method is called in clean. It is verifying if there is only a single interface is marked as primary.
        """
        primary_count = 0
        for interface in self.cleaned_data:
            if interface.get("primary", False):
                primary_count += 1
            if primary_count > 1:
                raise ValidationError(
                    "More then a single primary interface is not allowed!"
                )
        if len(self.cleaned_data) > 0 and primary_count != 1:
            raise ValidationError(
                "You need exactly one primary interface if you have one or more interfaces!"
            )

    def __verify_unique_mac_address(self):
        """
        This method is called in clean. It is verifying that all MAC addresses are unique inside the DB.
        """
        old_mac_addresses = list(
            self.instance.networkinterfaces.all().values_list("mac_address", flat=True)
        )
        new_mac_addresses = [
            instance.get("mac_address") for instance in self.cleaned_data
        ]
        if self.instance.has_bmc() and self.instance.bmc.mac != "":
            old_mac_addresses.append(self.instance.bmc.mac)

        if len(new_mac_addresses) != len(set(new_mac_addresses)):
            raise ValidationError("Duplicate MAC address detected!")

        for interface in self.cleaned_data:
            mac = interface.get("mac_address")
            if mac == "":
                continue
            if not is_unique_mac_address(mac, exclude=old_mac_addresses):
                raise ValidationError(
                    "MAC address '{}' is already used by '{}'!".format(
                        mac,
                        NetworkInterface.objects.get(mac_address=mac).machine.fqdn,  # type: ignore
                    ),
                )

    def __verify_unique_ip_address(self):
        """
        This method is called in clean. It is verifying if all IPs given are unique.
        """
        new_ip_addresses_4 = []
        for interface in self.cleaned_data:
            address = interface.get("ip_address_v4")
            if address != "":
                new_ip_addresses_4.append(address)
        new_ip_addresses_6 = []
        for interface in self.cleaned_data:
            address = interface.get("ip_address_v6")
            if address != "":
                new_ip_addresses_6.append(address)

        if len(new_ip_addresses_4) != len(set(new_ip_addresses_4)):
            raise ValidationError("Duplicate IPv4 address detected!")
        if len(new_ip_addresses_6) != len(set(new_ip_addresses_6)):
            raise ValidationError("Duplicate IPv6 address detected!")

        for interface in self.cleaned_data:
            ip_address_v4 = interface.get("ip_address_v4")
            ip_address_v6 = interface.get("ip_address_v6")
            network_interface_v4 = NetworkInterface.objects.filter(
                ip_address_v4=ip_address_v4
            )
            bmc_interface_v4 = BMC.objects.filter(ip_address_v4=ip_address_v4)
            network_interface_v6 = NetworkInterface.objects.filter(
                ip_address_v6=ip_address_v6
            )
            bmc_interface_v6 = BMC.objects.filter(ip_address_v6=ip_address_v6)
            if interface.get("id") is not None:
                network_interface_v4 = network_interface_v4.exclude(
                    id=interface.get("id").id
                )
                network_interface_v6 = network_interface_v6.exclude(
                    id=interface.get("id").id
                )
                bmc_interface_v4 = bmc_interface_v4.exclude(id=interface.get("id").id)
                bmc_interface_v6 = bmc_interface_v6.exclude(id=interface.get("id").id)
            if network_interface_v4.count() > 0 or bmc_interface_v4.count() > 0:
                raise ValidationError(
                    "IPv4 address already in use, please choose another one!"
                )
            if network_interface_v6.count() > 0 or bmc_interface_v6.count() > 0:
                raise ValidationError(
                    "IPv6 address already in use, please choose another one!"
                )


class NetworkInterfaceInline(admin.TabularInline):
    model = NetworkInterface
    extra = 0
    fk_name = "machine"
    readonly_fields = (
        "name",
        "ethernet_type",
        "driver_module",
    )
    formset = NetworkInterfaceInlineFormset
    form = NetworkInterfaceForm


class AnnotationInline(admin.TabularInline):
    model = Annotation
    extra = 0
    fk_name = "machine"
    readonly_fields = ("text", "reporter", "created")

    def has_add_permission(self, request, obj=None):
        """Annotations are added at machine detail view."""
        return False


class MachineAdminForm(forms.ModelForm):
    class Meta:
        model = Machine
        fields = "__all__"

    def __init__(self, *args, **kwargs) -> None:
        """Set primary MAC address and virtualization API type in the form fields."""
        instance = kwargs.get("instance", None)

        super(MachineAdminForm, self).__init__(*args, **kwargs)

        if instance:
            self.machine = instance

    def clean_fqdn(self) -> str:
        """Check if another machine has already this FQDN (except self)."""
        fqdn = self.cleaned_data["fqdn"]

        if hasattr(self, "machine"):
            # We do not reach below check, but we do if we would allow renaming at some point
            if Machine.objects.filter(fqdn=fqdn).exclude(pk=self.machine.pk):
                raise ValidationError("FQDN is already in use!")
        else:
            # new machine
            if Machine.objects.filter(fqdn=fqdn):
                raise ValidationError("FQDN is already in use!")
        return fqdn

    def clean(self) -> Optional[Dict[str, Any]]:
        """
        Verify that all information for a given machine is valid.
        """
        cleaned_data = self.cleaned_data
        # Individual field validation has already run, so FQDN can be assumed "clean".

        self.__verify_system_information_collection(cleaned_data)
        self.__verify_hypervisor_allowed_for_machine(cleaned_data)

        return cleaned_data

    def __verify_system_information_collection(self, cleaned_data: Dict[str, Any]):
        """
        This method is called in clean. It is verifying that there is no issue when attempting to collect system
        information via Ansible.
        """
        check_connectivity = cleaned_data.get("check_connectivity")
        collect_system_information = cleaned_data.get("collect_system_information")

        if (
            collect_system_information
            and check_connectivity != Machine.Connectivity.ALL
        ):
            self.add_error(
                "collect_system_information", "Connectivity check must set to 'Full'"
            )

    def __verify_hypervisor_allowed_for_machine(self, cleaned_data: Dict[str, Any]):
        """
        This method is called in clean. It is verifying that the machine can be a hypervisor.
        """
        hypervisor = cleaned_data.get("hypervisor")
        system = cleaned_data.get("system")
        if hypervisor and System.objects.filter(name=system, virtual=False):
            self.add_error(
                "system",
                "System type is not virtual. Only Virtual Machines may have a hypervisor",
            )
            self.add_error(
                "hypervisor",
                "System type {} is not virtual. Only Virtual Machines may have "
                "a hypervisor".format(system),
            )

        vm_dedicated_host = cleaned_data.get("vm_dedicated_host")
        if vm_dedicated_host and System.objects.filter(
            name=system, allowHypervisor=False
        ):
            self.add_error("system", "System type cannot serve as a hypervisor")
            self.add_error(
                "vm_dedicated_host", "System cannot be set as dedicated VM host"
            )


class MachineArchitectureFilter(admin.SimpleListFilter):
    title = "Architecture"

    parameter_name = "arch"

    def lookups(self, request: HttpRequest, model_admin) -> List[Tuple[int, str]]:  # type: ignore
        architectures = Architecture.objects.all()
        result = []

        for architecture in architectures:
            result.append((architecture.id, architecture.name))

        return result

    def queryset(
        self, request: HttpRequest, queryset: QuerySet["Machine"]
    ) -> Optional[QuerySet["Machine"]]:
        if self.value():
            return queryset.filter(architecture_id=self.value())  # type: ignore
        return None


class MachineSystemFilter(admin.SimpleListFilter):
    title = "System"

    parameter_name = "system"

    def lookups(self, request, model_admin):
        systems = System.objects.all()
        result = []

        result.append(("administrative", "Administrative"))
        result.append(("inactive", "Inactive"))

        for system in systems:
            result.append((system.id, system.name))

        return result

    def queryset(
        self, request: HttpRequest, queryset: QuerySet["Machine"]
    ) -> Optional[QuerySet["Machine"]]:
        value = self.value()
        if value:
            if value == "administrative":
                return queryset.filter(
                    Q(administrative=True) | Q(system__administrative=True)
                )
            elif value == "inactive":
                return queryset.filter(Q(active=False))
            else:
                return queryset.filter(system_id=self.value())  # type: ignore
        return None


class MachineDomainFilter(admin.SimpleListFilter):
    title = "Domain"

    parameter_name = "domain"

    def lookups(self, request: HttpRequest, model_admin) -> List[Tuple[int, str]]:  # type: ignore
        domains = Domain.objects.all()
        result = []

        for domain in domains:
            result.append((domain.id, domain.name))

        return result

    def queryset(
        self, request: HttpRequest, queryset: QuerySet["Machine"]
    ) -> Optional[QuerySet["Machine"]]:
        value = self.value()
        if value and value.isdigit():
            return queryset.filter(fqdn_domain_id=int(value))
        return None


class MachineGroupFilter(admin.SimpleListFilter):
    title = "Machine Groups"

    parameter_name = "machinegroup"

    def lookups(  # type: ignore
        self, request: HttpRequest, model_admin: ModelAdmin
    ) -> List[Tuple[int, str]]:
        machinegroups = MachineGroup.objects.all()
        result = []

        for group in machinegroups:
            result.append((group.id, group.name))

        return result

    def queryset(
        self, request: HttpRequest, queryset: QuerySet["Machine"]
    ) -> Optional[QuerySet["Machine"]]:
        value = self.value()
        if value and value.isdigit():
            return queryset.filter(group_id=int(value))
        return None


class MachineAdmin(admin.ModelAdmin):
    class Media:
        js = ("js/machine_admin.js",)

    form = MachineAdminForm

    list_display = (
        "fqdn",
        "enclosure",
        "architecture",
        "system",
        "reserved_by",
        # 'group',
        # 'active'
    )
    list_per_page = 50
    show_full_result_count = True
    list_max_show_all = 10000
    search_fields = ("fqdn",)
    list_filter = (
        MachineArchitectureFilter,
        MachineSystemFilter,
        MachineDomainFilter,
        MachineGroupFilter,
    )
    fieldsets = (
        (
            None,
            {
                "fields": (
                    ("fqdn", "enclosure"),
                    "architecture",
                    "system",
                    "group",
                    ("serial_number", "product_code"),
                    "comment",
                    "platform",
                    "contact_email",
                    "kernel_options",
                ),
            },
        ),
        (
            "PROPERTIES",
            {
                "fields": (
                    ("administrative", "nda"),
                    "autoreinstall",
                    "active",
                )
            },
        ),
        (
            "VIRTUALIZATION SERVER",
            {
                "fields": (
                    ("vm_dedicated_host", "vm_auto_delete"),
                    "vm_max",
                    "virt_api_int",
                ),
            },
        ),
        (
            "VIRTUALIZATION CLIENT",
            {
                "fields": ("hypervisor",),
            },
        ),
        (
            "MACHINE CHECKS",
            {"fields": ("check_connectivity", ("collect_system_information",))},
        ),
        (
            "DHCP",
            {
                "fields": (
                    "tftp_server",
                    "dhcp_filename",
                ),
            },
        ),
    )
    autocomplete_fields = ["hypervisor"]

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

    def add_view(self, request, form_url="", extra_context=None):
        """
        Return view for 'Add machine' and do not show inlines. This is due the fact that these
        objects need a related machine object (which doesn't exist yet) for several checks.
        """
        self.inlines = ()
        return super(MachineAdmin, self).add_view(request, form_url, extra_context)

    def get_fieldsets(self, request: HttpRequest, obj: Optional[Machine] = None):
        """Do not show 'VIRTUALIZATION' client/server forms if not appropriate"""
        fieldsets = super().get_fieldsets(request)
        if obj:
            fieldsets_ = ()
            for fieldset in fieldsets:
                if fieldset[0] == "VIRTUALIZATION SERVER":
                    if not obj.system.allowHypervisor:
                        continue
                if fieldset[0] == "VIRTUALIZATION CLIENT":
                    if not obj.system.virtual:
                        continue
                fieldsets_ += (fieldset,)  # type: ignore
            fieldsets = fieldsets_
        return fieldsets

    def change_view(
        self,
        request: HttpRequest,
        object_id: str,
        form_url="",
        extra_context: Optional[Dict[str, Any]] = None,
    ) -> Union[HttpResponseRedirect, TemplateResponse, HttpResponse]:
        """Return changes view with inlines for non-administrative systems."""
        machine = Machine.objects.get(pk=object_id)
        fence = None
        if machine.has_remotepower():
            fence = RemotePowerType.from_fence(machine.remotepower.fence_name)

        if not self.get_object(request, object_id):
            messages.add_message(
                request,
                messages.ERROR,
                "You are not allowed to edit this machine!",
                extra_tags="error",
            )

        self.inlines = (NetworkInterfaceInline, SerialConsoleInline)

        if machine.bmc_allowed():
            self.inlines += (BMCInline,)
            if hasattr(machine, "bmc"):
                if not fence or fence.device == "bmc":
                    self.inlines += (RemotePowerInlineBMC,)
        if machine.is_virtual_machine():
            self.inlines += (RemotePowerInlineHypervisor,)
        else:
            # Only show rpower device to add/modify if we do not
            # have one yet or if it's a rpower_device already
            if not fence or fence.device == "rpower_device":
                self.inlines += (RemotePowerInlineRpower,)

        if not machine.system.administrative:
            self.inlines += (AnnotationInline,)

        return super(MachineAdmin, self).change_view(
            request, object_id, form_url, extra_context
        )

    def save_formset(self, request: HttpRequest, form, formset, change) -> None:
        formset.save()
        machine = form.save(commit=False)
        if (
            machine.bmc_allowed()
            and hasattr(machine, "bmc")
            and not hasattr(machine, "remotepower")
        ):
            machine.remotepower = RemotePower(
                machine.bmc.fence_name, machine, machine.bmc
            )
            machine.bmc.save()
            machine.remotepower.save()
            machine.save()


admin.site.register(Machine, MachineAdmin)


class ArchsInline(admin.TabularInline):
    model = DomainAdmin
    fields = (
        "arch",
        "contact_email",
    )


class DomainAdminAdmin(admin.ModelAdmin):
    list_display = ("name", "cobbler_server_list", "tftp_server", "cscreen_server")
    inlines = (ArchsInline,)

    def cobbler_server_list(self, obj: "Domain"):
        """Return DHCP server FQDN as string."""
        cobbler_server = obj.cobbler_server
        return cobbler_server.fqdn if cobbler_server else "-"

    def delete_model(
        self, request: HttpRequest, obj: Optional["Domain"] = None
    ) -> None:
        if obj is None:
            messages.error(request, "You must specify a Domain to delete.")
            return
        try:
            obj.delete()
        except ValidationError as e:
            messages.error(request, e.message)

    def has_delete_permission(
        self, request: HttpRequest, obj: Optional["Domain"] = None
    ) -> bool:
        if obj is not None and obj.machine_set.count() > 0:
            return False
        return super().has_delete_permission(request, obj=obj)


admin.site.register(Domain, DomainAdminAdmin)


class EnclosureAdmin(admin.ModelAdmin):
    readonly_fields = ("location_room", "location_rack", "location_rack_position")
    list_display = ("name", "machine_count", "platform_name")
    search_fields = ("name",)

    def machine_count(self, obj: Enclosure) -> int:
        """Return machine counter of enclosure."""
        return obj.machine_set.count()

    def platform_name(self, obj: Enclosure) -> Optional[str]:
        """Return name of enclosures platform."""
        platform = obj.platform
        if platform:
            return platform.name
        return None


admin.site.register(Enclosure, EnclosureAdmin)


class RemotePowerDeviceAdmin(admin.ModelAdmin):
    form = RemotePowerDeviceAPIForm
    list_display = ["fqdn", "fence_name"]


admin.site.register(RemotePowerDevice, RemotePowerDeviceAdmin)


class ServerConfigAdmin(admin.ModelAdmin):
    list_display = ("key", "augmented_value")
    search_fields = ("key", "value")

    # https://medium.com/@hakibenita/how-to-add-custom-action-buttons-to-django-admin-8d266f5b0d41
    def get_urls(self) -> List[URLPattern]:
        """Add custom URLs to server configuration admin view."""
        urls = super(ServerConfigAdmin, self).get_urls()
        custom_urls = [
            re_path(
                r"^(?P<serverconfig_id>.+)/switch/$",
                self.admin_site.admin_view(self.process_boolean_switch),
                name="boolean_switch",
            ),
        ]
        return custom_urls + urls

    def process_boolean_switch(
        self, request: HttpRequest, serverconfig_id: int, *args: Any, **kwargs: Any
    ) -> HttpResponseRedirect:
        """Enable/disable value."""
        action = request.GET.get("action", None)

        if (action is not None) and (action in {"enable", "disable"}):
            try:
                configuration = ServerConfig.objects.get(pk=serverconfig_id)

                if action == "enable":
                    configuration.value = "bool:true"
                elif action == "disable":
                    configuration.value = "bool:false"

                configuration.save()
                messages.info(
                    request, "Successfully {}d: '{}'.".format(action, configuration.key)
                )

            except Exception as e:
                messages.error(request, str(e), extra_tags="error")

        return redirect("admin:data_serverconfig_changelist")

    def augmented_value(self, obj):
        """Add buttons for boolean values ('bool:true' or 'bool:false')."""
        if obj.value.lower() == "bool:false":
            button = _boolean_icon(False)
            button += (
                ' <span class="help">(<a href="{}?action=enable">Enable</a>)</span>'
            )
            return format_html(button, reverse("admin:boolean_switch", args=[obj.pk]))
        elif obj.value.lower() == "bool:true":
            button = _boolean_icon(True)
            button += (
                ' <span class="help">(<a href="{}?action=disable">Disable</a>)</span>'
            )
            return format_html(button, reverse("admin:boolean_switch", args=[obj.pk]))

        return obj.value


admin.site.register(ServerConfig, ServerConfigAdmin)


class PlatformAdmin(admin.ModelAdmin):
    list_display = ("name", "get_vendor", "get_enclosure_count", "is_cartridge")
    list_per_page = 50
    search_fields = ("name",)
    show_full_result_count = True
    list_max_show_all = 1000


admin.site.register(Platform, PlatformAdmin)


class ArchitectureAdmin(admin.ModelAdmin):
    list_display = ("name", "get_machine_count", "dhcp_filename")

    def delete_model(
        self, request: HttpRequest, obj: Optional["Architecture"] = None
    ) -> None:
        if obj is None:
            messages.error(request, "You must specify an Architecture to delete.")
            return
        try:
            obj.delete()
        except ValidationError as e:
            messages.error(request, e.message)

    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        if obj is not None and obj.machine_set.count() > 0:
            return False
        return super(ArchitectureAdmin, self).has_delete_permission(request, obj=obj)


admin.site.register(Architecture, ArchitectureAdmin)


class SerialConsoleTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "command")


admin.site.register(SerialConsoleType, SerialConsoleTypeAdmin)


class SystemAdmin(admin.ModelAdmin):
    list_display = ("name", "virtual", "administrative")


admin.site.register(System, SystemAdmin)


class MachineGroupMembershipInline(admin.TabularInline):
    model = MachineGroupMembership
    extra = 0


class MachinesInline(admin.TabularInline):
    model = Machine
    fields = ("fqdn",)
    readonly_fields = ("fqdn",)

    def has_add_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False


class MachineGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "machines", "dhcp_filename")
    inlines = (MachinesInline, MachineGroupMembershipInline)

    def machines(self, obj: MachineGroup) -> str:
        machines = Machine.objects.filter(group=obj)
        output = ", ".join([machine.fqdn for machine in machines])
        return output


admin.site.register(MachineGroup, MachineGroupAdmin)
admin.site.register(Vendor)
