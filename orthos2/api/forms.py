import logging
from typing import Any, Dict, List, Optional, Tuple

from django import forms
from django.db import models
from django.forms import Field, inlineformset_factory  # type: ignore
from django.forms.fields import (
    BooleanField,
    CharField,
    ChoiceField,
    DateField,
    DecimalField,
    IntegerField,
)
from django.forms.models import ModelChoiceIteratorValue
from django.template.defaultfilters import slugify

from orthos2.data.models import (
    Architecture,
    Enclosure,
    Machine,
    MachineGroup,
    NetworkInterface,
    RemotePower,
    RemotePowerDevice,
    SerialConsole,
    SerialConsoleType,
    System,
)
from orthos2.data.models.domain import validate_domain_ending
from orthos2.data.validators import validate_mac_address
from orthos2.frontend.forms.reservemachine import ReserveMachineForm
from orthos2.frontend.forms.virtualmachine import VirtualMachineForm
from orthos2.utils.misc import is_unique_mac_address
from orthos2.utils.remotepowertype import get_remote_power_type_choices

logger = logging.getLogger("api")


class BaseAPIForm:
    def form_field_to_dict(
        self,
        form_field: Field,
        name: str,
        prompt: Optional[Any] = None,
        initial: Optional[str] = None,
        required: Optional[bool] = None,
    ) -> Dict[str, Any]:
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
                    initial = "y" if form_field.initial else "n"
                else:
                    initial = str(form_field.initial)
            else:
                initial = None

        if not required:
            required = form_field.required

        field: Dict[str, Any] = {
            "prompt": prompt,
            "initial": initial,
            "required": required,
        }

        if isinstance(form_field, CharField):
            field["type"] = "STRING"

        elif isinstance(form_field, DateField):
            field["type"] = "DATE"

        elif isinstance(form_field, BooleanField):
            field["type"] = "BOOLEAN"

        elif isinstance(form_field, (DecimalField, IntegerField)):
            field["type"] = "INTEGER"
            field["max"] = form_field.max_value
            field["min"] = form_field.min_value

        elif isinstance(form_field, ChoiceField):
            field["type"] = "SELECTION"
            field["items"] = []

            for choice in form_field.choices:  # type: ignore
                if isinstance(choice[0], ModelChoiceIteratorValue):
                    field["items"].append(  # type: ignore
                        {
                            slugify(choice[0].value): {  # type: ignore
                                "label": choice[1],
                                "value": choice[0].value,  # type: ignore
                            }
                        }
                    )
                else:
                    field["items"].append(  # type: ignore
                        {
                            slugify(choice[0]): {  # type: ignore
                                "label": choice[1],
                                "value": choice[0],
                            }
                        }
                    )

        return field

    def as_dict(self) -> Dict[str, Any]:
        """Generate and return form as dictionary."""
        result: Dict[str, Any] = {}

        for name, field in self.fields.items():  # type: ignore
            result[name] = self.form_field_to_dict(field, name)  # type: ignore

        return result


class ReserveMachineAPIForm(ReserveMachineForm, BaseAPIForm):
    def as_dict(self) -> Dict[str, Any]:
        """Generate and return form as dictionary."""
        result: Dict[str, Any] = {}

        for name, field in self.fields.items():
            result[name] = self.form_field_to_dict(field, name)

        result["until"]["prompt"] = "Duration (days)"
        result["until"]["type"] = "INTEGER"

        result["username"] = {
            "type": "STRING",
            "prompt": "User for which you want to reserve",
            "initial": self.fields["username"].initial,
            "required": True,
        }
        return result

    def get_order(self) -> List[str]:
        """Return input order."""
        return ["username", "reason", "until"]


class VirtualMachineAPIForm(VirtualMachineForm, BaseAPIForm):
    def as_dict(self, host: Optional[Machine]) -> Dict[str, Any]:  # type: ignore
        """Generate and return form as dictionary."""
        result: Dict[str, Any] = {}

        for name, field in self.fields.items():
            result[name] = self.form_field_to_dict(field, name)

        result["host"] = {
            "type": "STRING",
            "prompt": "Host FQDN",
            "initial": host.fqdn,  # type: ignore
            "required": True,
        }

        return result

    def get_order(self) -> List[str]:
        """Return input order."""
        return [
            "host",
            "system",
            "architecture",
            "ram_amount",
            "image",
            "disk_size",
            "networkinterfaces",
            "uefi_boot",
            "vnc",
            "parameters",
        ]


def get_architectures() -> List[Tuple[int, str]]:
    """Return architectures choice tuple."""
    architectures: List[Tuple[int, str]] = []
    for architecture in (
        Architecture.objects.all().values("id", "name").order_by("name")
    ):
        architectures.append((architecture["id"], architecture["name"]))
    return architectures


def get_systems() -> List[Tuple[int, str]]:
    """Return systems choice tuple."""
    systems: List[Tuple[int, str]] = []
    for system in System.objects.all().values("id", "name").order_by("name"):
        systems.append((system["id"], system["name"]))
    return systems


def get_machinegroups() -> List[Tuple[int, str]]:
    """Return machine group choice tuple."""
    groups = [("none", "None")]
    for group in MachineGroup.objects.all().values("id", "name").order_by("name"):
        groups.append((group["id"], group["name"]))  # type: ignore
    return groups  # type: ignore


class MachineAPIForm(forms.Form, BaseAPIForm):
    def clean_fqdn(self) -> str:
        """Check whether `fqdn` already exists."""
        fqdn = self.cleaned_data["fqdn"]
        if Machine.objects.filter(fqdn__iexact=fqdn).count() != 0:
            self.add_error("fqdn", "FQDN is already in use!")
        return fqdn

    def clean_mac_address(self) -> str:
        """Check whether `mac_address` already exists."""
        mac_address = self.cleaned_data["mac_address"]
        if not is_unique_mac_address(mac_address):
            self.add_error(
                "mac_address",
                "MAC address '{}' is already used by '{}'!".format(
                    mac_address,
                    NetworkInterface.objects.get(
                        mac_address=mac_address
                    ).machine.fqdn,  # type: ignore
                ),
            )
        return mac_address

    def clean_enclosure(self) -> str:
        """Set the proper `enclosure` value."""
        enclosure = self.cleaned_data["enclosure"]
        if not enclosure:
            enclosure = None
        return enclosure  # type: ignore

    def clean_group_id(self) -> str:
        """Set `group_id` to None if 'None' is selected."""
        group_id = self.cleaned_data["group_id"]
        if group_id == "none":
            group_id = None
        return group_id  # type: ignore

    def clean(self) -> Dict[str, Any]:
        """
        Get or create the enclosure.

        Only allow collect system information if connectivity is set to `Full`.
        """
        cleaned_data = super(MachineAPIForm, self).clean()

        enclosure = cleaned_data["enclosure"]  # type: ignore
        if enclosure:
            try:
                enclosure, _created = Enclosure.objects.get_or_create(name=enclosure)
            except Exception as e:
                logger.exception(e)
                self.add_error("enclosure", "Something went wrong!")
        cleaned_data["enclosure"] = enclosure  # type: ignore

        # If no connectivity check is given, assume none should be checked
        check_connectivity = int(cleaned_data.get("check_connectivity", 0))  # type: ignore
        collect_system_information = cleaned_data["collect_system_information"]  # type: ignore

        if (
            collect_system_information
            and check_connectivity != Machine.Connectivity.ALL
        ):
            self.add_error(
                "collect_system_information", "Needs full connectivity check!"
            )

        return cleaned_data  # type: ignore

    fqdn = forms.CharField(
        label="FQDN",
        max_length=200,
        validators=[validate_domain_ending],
    )

    enclosure = forms.CharField(
        max_length=200,
        required=False,
    )

    mac_address = forms.CharField(
        label="MAC address", validators=[validate_mac_address], required=False
    )

    architecture_id = forms.ChoiceField(
        label="Architecture",
        choices=get_architectures,
    )

    system_id = forms.ChoiceField(
        label="System",
        choices=get_systems,
    )

    group_id = forms.ChoiceField(
        label="Machine group",
        choices=get_machinegroups,
        initial=0,
    )

    nda = forms.BooleanField(
        label="NDA hardware",
        required=False,
        initial=False,
    )

    administrative = forms.BooleanField(
        label="Administrative machine",
        required=False,
        initial=False,
    )

    check_connectivity = forms.ChoiceField(
        label="Check connectivity",
        choices=Machine.CONNECTIVITY_CHOICE,
        initial=Machine.Connectivity.ALL,
    )

    collect_system_information = forms.BooleanField(
        label="Collect system information",
        required=False,
        initial=True,
    )

    hypervisor_fqdn = forms.CharField(
        label="Hypervisor",
        max_length=256,
        required=False,
    )

    def get_order(self) -> List[str]:
        """Return input order."""
        return [
            "fqdn",
            "enclosure",
            "mac_address",
            "architecture_id",
            "system_id",
            "group_id",
            "hypervisor_fqdn",
            "nda",
            "administrative",
            "check_connectivity",
            "collect_system_information",
        ]


class DeleteMachineAPIForm(forms.Form, BaseAPIForm):
    def clean_fqdn(self) -> str:
        """Check whether `fqdn` already exists."""
        fqdn = self.cleaned_data["fqdn"]
        if Machine.objects.filter(fqdn__iexact=fqdn).count() == 0:
            self.add_error("fqdn", "FQDN does not exist!")
        return fqdn

    fqdn = forms.CharField(
        label="FQDN",
        max_length=200,
    )

    def get_order(self) -> List[str]:
        """Return input order."""
        return [
            "fqdn",
        ]


class SerialConsoleAPIForm(forms.Form, BaseAPIForm):
    @staticmethod
    def get_serial_type_choices() -> List[Tuple[int, str]]:
        """Return serial console type  choice tuple."""
        serial_types: List[Tuple[int, str]] = []
        for serial_type in (
            SerialConsoleType.objects.all().values("id", "name").order_by("name")
        ):
            serial_types.append((serial_type["id"], serial_type["name"]))
        return serial_types

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        machine = kwargs.pop("machine", None)
        self.machine = machine

        super(SerialConsoleAPIForm, self).__init__(*args, **kwargs)

        self._query_fields = (
            "stype",
            "baud_rate",
            "kernel_device",
            "kernel_device_num",
            "console_server",
            "port",
            "command",
            "comment",
        )

        SerialConsoleFormSet = inlineformset_factory(  # type: ignore
            Machine, SerialConsole, fields=self._query_fields, fk_name="machine"
        )
        formset = SerialConsoleFormSet(instance=machine)  # type: ignore

        self.fields = formset.form().fields  # type: ignore
        self.fields["stype"].empty_label = None  # type: ignore
        self.fields["stype"].choices = self.get_serial_type_choices  # type: ignore
        self.fields["baud_rate"].initial = 5
        self.fields["kernel_device"].initial = 0
        self.fields["kernel_device_num"].min_value = 0  # type: ignore
        self.fields["kernel_device_num"].max_value = 1024  # type: ignore
        self.fields["console_server"].empty_label = "None"  # type: ignore

    def clean(self) -> Dict[str, Any]:
        """Add the machine to cleaned data for further processing."""
        cleaned_data = super(SerialConsoleAPIForm, self).clean()
        cleaned_data["machine"] = self.machine  # type: ignore
        serialconsole = SerialConsole(**cleaned_data)  # type: ignore
        serialconsole.clean()
        return cleaned_data  # type: ignore

    def get_order(self) -> Tuple[str, str, str, str, str, str, str, str]:
        """Return input order."""
        return self._query_fields


class DeleteSerialConsoleAPIForm(forms.Form, BaseAPIForm):
    def clean_fqdn(self) -> str:
        """Check whether `fqdn` already exists."""
        fqdn = self.cleaned_data["fqdn"]
        if Machine.objects.filter(fqdn__iexact=fqdn).count() == 0:
            self.add_error("fqdn", "FQDN does not exist!")
        return fqdn

    fqdn = forms.CharField(
        label="FQDN",
        max_length=200,
    )

    def get_order(self) -> List[str]:
        """Return input order."""
        return [
            "fqdn",
        ]


class AnnotationAPIForm(forms.Form, BaseAPIForm):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        machine = kwargs.pop("machine", None)
        self.machine = machine

        super(AnnotationAPIForm, self).__init__(*args, **kwargs)

    text = forms.CharField(
        label="Text",
        max_length=1024,
    )

    def get_order(self) -> List[str]:
        """Return input order."""
        return [
            "text",
        ]


class BMCAPIForm(forms.Form, BaseAPIForm):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        machine = kwargs.pop("machine", None)
        self.machine = machine

        super().__init__(*args, **kwargs)
        self._query_fields = (
            "fqdn",
            "mac",
            "username",
            "password",
            "fence_name",
        )
        self.fields["fence_name"] = forms.ChoiceField(
            choices=get_remote_power_type_choices("BMC"),
            label="Fence Agent",
        )

    username = forms.CharField(label="BMC Username", max_length=256, required=False)
    password = forms.CharField(
        label="Password",
        max_length=256,
        required=False,
        widget=forms.PasswordInput(render_value=True),
    )
    fqdn = forms.CharField(
        label="FQDN",
        max_length=256,
    )
    mac = forms.CharField(
        label="MAC Address",
        max_length=256,
    )
    fence_name = forms.ChoiceField(
        choices=[],
        label="Fence Agent",
    )

    def get_order(self) -> Tuple[str, str, str, str, str]:
        """Return input order."""
        return self._query_fields


class RemotePowerAPIForm(forms.Form, BaseAPIForm):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        machine = kwargs.pop("machine", None)
        self.machine = machine

        super(RemotePowerAPIForm, self).__init__(*args, **kwargs)

        self._query_fields = (
            "fence_name",
            "remote_power_device",
            "port",
            "comment",
        )

        RemotePowerFormSet = inlineformset_factory(  # type: ignore
            Machine, RemotePower, fields=self._query_fields, fk_name="machine"
        )
        formset = RemotePowerFormSet(instance=machine)  # type: ignore

        self.fields = formset.form().fields  # type: ignore
        self.fields["remote_power_device"].empty_label = "None"  # type: ignore
        self.fields["fence_name"].required = False

    def clean(self) -> Optional[Dict[str, Any]]:
        """Add the machine to cleaned data for further processing."""
        cleaned_data = super(RemotePowerAPIForm, self).clean()
        if cleaned_data is None:
            return None
        cleaned_data["machine"] = self.machine
        remotepower = RemotePower(**cleaned_data)
        remotepower.clean()
        return cleaned_data

    def get_order(self) -> Tuple[str, str, str, str]:
        """Return input order."""
        return self._query_fields


class RemotePowerDeviceAPIForm(forms.ModelForm, BaseAPIForm):  # type: ignore
    class Meta:
        model = RemotePowerDevice
        fields = ["fqdn", "mac", "username", "password", "fence_name", "url"]

    remotepower_type_choices = get_remote_power_type_choices("rpower_device")

    fence_name = models.CharField(  # type: ignore
        choices=remotepower_type_choices,
        max_length=255,
        verbose_name="Fence Agent",
    )

    password = forms.CharField(
        label="Password",
        max_length=256,
        required=True,
        widget=forms.PasswordInput(render_value=True),
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)  # type: ignore
        remote_power_choices = get_remote_power_type_choices("rpower_device")
        self.fields["fence_name"].choices = remote_power_choices  # type: ignore
        # Automatic Widget selection doesn't seem to work in this scenario sadly
        self.fields["fence_name"].widget = forms.Select(choices=remote_power_choices)


class DeleteRemotePowerAPIForm(forms.Form, BaseAPIForm):
    def clean_fqdn(self) -> str:
        """Check whether `fqdn` already exists."""
        fqdn = self.cleaned_data["fqdn"]
        if Machine.objects.filter(fqdn__iexact=fqdn).count() == 0:
            self.add_error("fqdn", "FQDN does not exist!")
        return fqdn

    fqdn = forms.CharField(
        label="FQDN",
        max_length=200,
    )

    def get_order(self) -> List[str]:
        """Return input order."""
        return [
            "fqdn",
        ]


class DeleteRemotePowerDeviceAPIForm(forms.Form, BaseAPIForm):
    def clean_fqdn(self) -> str:
        """Check whether `fqdn` already exists."""
        fqdn = self.cleaned_data["fqdn"]
        if RemotePowerDevice.objects.filter(fqdn__iexact=fqdn).count() == 0:  # type: ignore
            self.add_error("fqdn", "No remotepowerdevice with this FQDN")
        return fqdn

    fqdn = forms.CharField(
        label="FQDN",
        max_length=255,
    )

    def get_order(self) -> List[str]:
        """Return input order."""
        return [
            "fqdn",
        ]
