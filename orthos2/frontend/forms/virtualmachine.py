"""
This module contains all code to create a new virtual machine.
"""

from typing import Any

from django import forms
from django.conf import settings

from orthos2.data.models import System


class VirtualMachineForm(forms.Form):
    """
    Form to create a new virtual machine.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        virtualization_api = kwargs.pop("virtualization_api", None)

        super(VirtualMachineForm, self).__init__(*args, **kwargs)

        if settings.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3":
            name_regex = r"\bKVM\b"
        elif (
            settings.DATABASES["default"]["ENGINE"]
            == "django.db.backends.postgresql_psycopg2"
        ):
            name_regex = r"\yKVM\y"
        else:
            raise ValueError("Unsupported database driver!")
        self.fields["system"].choices = [  # type: ignore
            (system.pk, system.name)
            for system in System.objects.filter(virtual=True, name__regex=name_regex)
        ]
        if virtualization_api is None:
            raise ValueError(
                'VirtualMachineForm requires "virtualization_api" (an instance of "VirtualizationAPI") '
                "as a kwarg."
            )
        architectures, image_list = virtualization_api.get_image_list()
        self.fields["architecture"].choices = [(architectures[0], architectures[0])]  # type: ignore
        self.fields["image"].choices = [("none", "None")] + image_list  # type: ignore

    def clean(self):
        """Set `image` to None; cast `decimal.Decimal()` to `int`."""
        cleaned_data = super(VirtualMachineForm, self).clean()

        if cleaned_data["image"] == "none":
            cleaned_data["image"] = None

        cleaned_data["networkinterfaces"] = int(cleaned_data["networkinterfaces"])
        cleaned_data["ram_amount"] = int(cleaned_data["ram_amount"])
        cleaned_data["disk_size"] = int(cleaned_data["disk_size"])

        return cleaned_data

    uefi_boot = forms.BooleanField(label="Use UEFI boot", required=False, initial=False)

    ram_amount = forms.DecimalField(
        label="Memory (MB)",
        required=True,
        initial=2048,
        max_value=16384,
        min_value=512,
        help_text="Value between 512MB and 16384MB.",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )

    image = forms.ChoiceField(
        required=True,
        choices=[],
        widget=forms.Select(attrs={"class": "custom-select form-control"}),
    )

    networkinterfaces = forms.DecimalField(
        required=True,
        initial=1,
        max_value=5,
        min_value=1,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )

    parameters = forms.CharField(
        required=False,
        help_text="e.g. '--cdrom /dev/cdrom'",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    system = forms.ChoiceField(
        required=True,
        choices=[],
        widget=forms.Select(attrs={"class": "custom-select form-control"}),
        initial=0,
    )

    architecture = forms.ChoiceField(
        required=True,
        choices=[],
        widget=forms.Select(attrs={"class": "custom-select form-control"}),
        initial=0,
    )

    disk_size = forms.DecimalField(
        label="Disk size (GB)",
        required=True,
        initial=30,
        max_value=100,
        min_value=30,
        help_text="Value between 30GB and 100GB; applies only if no image is selected.",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )

    vnc = forms.BooleanField(label="Enable VNC", required=False, initial=False)
