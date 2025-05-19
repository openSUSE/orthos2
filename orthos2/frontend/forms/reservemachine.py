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
        super(ReserveMachineForm, self).__init__(*args, **kwargs)
        self.fields["reason"].initial = reason
        if until is not None:
            self.fields["until"].initial = date_format(
                until, format=settings.SHORT_DATE_FORMAT
            )
        self.fields["username"].initial = username

    reason = forms.CharField(
        widget=forms.Textarea(attrs={"class": "form-control"}),
        help_text="Please provide a reason why you reserve this machine.",
    )

    until = forms.DateField(
        widget=forms.TextInput(
            attrs={"id": "datepicker", "size": "10", "class": "form-control"}
        ),
        help_text="Format: YYYY-MM-DD (TZ: "
        + timezone.get_default_timezone_name()
        + "). Type '9999-12-31' for infinite reservation (superusers only).",
    )

    username = forms.CharField(widget=forms.HiddenInput(), required=False)

    def clean(self) -> None:
        cleaned_data = super(ReserveMachineForm, self).clean()
        if cleaned_data is None:
            # It may be that a superclass didn't return cleaned data (as this is optional)
            # https://docs.djangoproject.com/en/4.2/ref/forms/validation/#cleaning-and-validating-fields-that-depend-on-each-other
            cleaned_data = self.cleaned_data
        reserved_until = cleaned_data.get("until")

        if not reserved_until:
            # return due to further checks which needs datetime object
            return

        if reserved_until == datetime.date.max:
            pass

        elif reserved_until <= datetime.datetime.now().date():
            self.add_error(
                "until", "Reservation date must be in the future (min. 1 day)."
            )

        elif reserved_until > (
            datetime.datetime.now().date() + datetime.timedelta(days=90)
        ):
            self.add_error("until", "Reservation period is limited (max. 90 days).")
