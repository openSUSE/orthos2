"""
This module contains the logic to help restoring the password of a user.
"""

from typing import Any

from django import forms


class PasswordRestoreForm(forms.Form):
    """
    Form to restore the password of a user with the built-in authentication provider.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        username = kwargs.pop("username", None)

        super(PasswordRestoreForm, self).__init__(*args, **kwargs)

        if username is not None:
            self.fields["login"].initial = username

    login = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    email = forms.EmailField(
        max_length=64,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
