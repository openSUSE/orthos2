from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

from django import forms
from django.contrib import admin, messages
from django.contrib.admin import ModelAdmin
from django.core.exceptions import ValidationError
from django.db.models import Q, QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse

from orthos2.data.models import (
    Annotation,
    Architecture,
    Domain,
    Machine,
    System,
)

if TYPE_CHECKING:
    from django.contrib.auth.models import User


class AnnotationInline(admin.TabularInline):  # type: ignore
    model = Annotation
    extra = 0
    fk_name = "machine"
    readonly_fields = ("text", "reporter", "created")

    def has_add_permission(self, request: HttpRequest, obj=None):  # type: ignore
        """Annotations are added at machine detail view."""
        return False


class MachineAdminForm(forms.ModelForm):  # type: ignore
    class Meta:  # type: ignore
        model = Machine
        fields = "__all__"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Set primary MAC address and virtualization API type in the form fields."""
        instance = kwargs.get("instance", None)

        super(MachineAdminForm, self).__init__(*args, **kwargs)  # type: ignore

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

    def __verify_system_information_collection(
        self, cleaned_data: Dict[str, Any]
    ) -> None:
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

    def __verify_hypervisor_allowed_for_machine(
        self, cleaned_data: Dict[str, Any]
    ) -> None:
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
        result: List[Tuple[int, str]] = []

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

    def lookups(
        self, request: HttpRequest, model_admin: "ModelAdmin[System]"
    ) -> List[Tuple[str, str]]:
        systems = System.objects.all()
        result: List[Tuple[str, str]] = []

        result.append(("administrative", "Administrative"))
        result.append(("inactive", "Inactive"))

        for system in systems:
            result.append((str(system.id), system.name))

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

    def lookups(  # type: ignore
        self,
        request: HttpRequest,
        model_admin: "ModelAdmin[Domain]",
    ) -> List[Tuple[int, str]]:
        domains = Domain.objects.all()
        result: List[Tuple[int, str]] = []

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


class MachineAdmin(admin.ModelAdmin):  # type: ignore
    class Media:
        js = ("js/machine_admin.js",)

    form = MachineAdminForm

    list_display = (
        "fqdn",
        "enclosure",
        "architecture",
        "system",
        "reserved_by",
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
    )
    fieldsets = (
        (
            None,
            {
                "fields": (
                    ("fqdn", "enclosure"),
                    "architecture",
                    "system",
                    ("serial_number", "product_code"),
                    "comment",
                    "device_type",
                    "contact_email",
                    "kernel_options",
                    "netbox_id",
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

    def get_queryset(self, request: HttpRequest) -> "QuerySet[Machine]":
        """Filter machine list. Only superusers are authorized to see/edit machines."""
        queryset: "QuerySet[Machine]" = super(  # type: ignore
            MachineAdmin, self
        ).get_queryset(request)
        user: "User" = request.user  # type: ignore

        if user.is_superuser:  # type: ignore
            return queryset

        return Machine.objects.none()

    def add_view(
        self,
        request: HttpRequest,
        form_url: str = "",
        extra_context: Optional[Dict[str, Any]] = None,
    ):
        """
        Return view for 'Add machine' and do not show inlines. This is due the fact that these
        objects need a related machine object (which doesn't exist yet) for several checks.
        """
        MachineAdmin.inlines = ()
        return super(MachineAdmin, self).add_view(request, form_url, extra_context)

    def get_fieldsets(self, request: HttpRequest, obj: Optional[Machine] = None):
        """Do not show 'VIRTUALIZATION' client/server forms if not appropriate"""
        fieldsets = super().get_fieldsets(request)  # type: ignore
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
        form_url: str = "",
        extra_context: Optional[Dict[str, Any]] = None,
    ) -> Union[HttpResponseRedirect, TemplateResponse, HttpResponse]:
        """Return changes view with inlines for non-administrative systems."""
        machine = Machine.objects.get(pk=object_id)

        if not self.get_object(request, object_id):
            messages.add_message(
                request,
                messages.ERROR,
                "You are not allowed to edit this machine!",
                extra_tags="error",
            )

        MachineAdmin.inlines = ()

        if not machine.system.administrative:
            MachineAdmin.inlines += (AnnotationInline,)

        return super(MachineAdmin, self).change_view(
            request, object_id, form_url, extra_context
        )


admin.site.register(Machine, MachineAdmin)  # type: ignore
