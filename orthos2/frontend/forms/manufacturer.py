"""
This module contains the form used to create/edit a Manufacturer.
"""

from typing import Any

from django import forms

from orthos2.data.models import Manufacturer


class ManufacturerForm(forms.ModelForm):  # type: ignore
    class Meta:  # type: ignore
        model = Manufacturer
        fields = ["name", "netbox_id"]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.netbox_id > 0:
            self.fields["name"].disabled = True
