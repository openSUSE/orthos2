"""
This module contains all logic to reserve a machine for a user.
"""

import datetime
from typing import Any

from django import forms
from django.conf import settings
from django.utils import timezone
from django.utils.formats import date_format


class ReserveMachineForm(forms.Form):
    """
    Form to reserve a machine for a user.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        reason = kwargs.pop("reason", None)
        until = kwargs.pop("until", None)
        username = kwargs.pop("username", None)
        permanently = kwargs.pop("permanently", False)
        super(ReserveMachineForm, self).__init__(*args, **kwargs)
        self.fields["reason"].initial = reason
        if until is not None:
            self.fields["until"].initial = date_format(
                until, format=settings.SHORT_DATE_FORMAT
            )
        self.fields["username"].initial = username
        self.fields["permanently"].initial = permanently

    reason = forms.CharField(
        widget=forms.Textarea(attrs={"class": "form-control"}),
        help_text="Please provide a reason why you reserve this machine.",
    )

    until = forms.DateField(
        required=False,
        widget=forms.TextInput(
            attrs={"id": "datepicker", "size": "10", "class": "form-control"}
        ),
        help_text="Format: YYYY-MM-DD (TZ: "
        + timezone.get_default_timezone_name()
        + "). Max 90 days. Leave empty when reserving permanently.",
    )

    permanently = forms.BooleanField(
        required=False,
        label="Reserve permanently (superusers only)",
        widget=forms.CheckboxInput(
            attrs={"class": "form-check-input", "id": "permanently"}
        ),
    )

    username = forms.CharField(widget=forms.HiddenInput(), required=False)

    def clean(self) -> None:
        cleaned_data = super(ReserveMachineForm, self).clean()
        if cleaned_data is None:
            cleaned_data = self.cleaned_data
        permanently = cleaned_data.get("permanently", False)
        until = cleaned_data.get("until")

        if permanently:
            cleaned_data["until"] = None
        elif not until:
            self.add_error(
                "until",
                "Please provide a reservation date or check 'Reserve permanently'.",
            )
        elif until <= datetime.datetime.now().date():
            self.add_error(
                "until", "Reservation date must be in the future (min. 1 day)."
            )
        elif until > (datetime.datetime.now().date() + datetime.timedelta(days=90)):
            self.add_error("until", "Reservation period is limited (max. 90 days).")


class ReserveMachineForUserForm(ReserveMachineForm):
    """
    Form for superusers to reserve a machine on behalf of another user.
    """

    field_order = ["machine", "reason", "until", "permanently"]

    machine = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}),
        help_text="Enter the fully qualified domain name (FQDN) of the machine to reserve.",
        label="Machine FQDN",
    )
