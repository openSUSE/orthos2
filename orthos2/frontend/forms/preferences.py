"""
This module contains the logic to show the preferences of a user.
"""

from django import forms


class PreferencesForm(forms.Form):
    """
    Form to show the preferences of a user with the built-in authentication provider.
    """

    def clean(self) -> None:
        cleaned_data = super(PreferencesForm, self).clean()
        new_password = cleaned_data.get("new_password")  # type: ignore
        new_password2 = cleaned_data.get("new_password2")  # type: ignore

        if len(new_password) < 8:  # type: ignore
            self.add_error(
                "new_password",
                "Password is too short. It must contain at least 8 characters.",
            )

        if new_password != new_password2:
            self.add_error(
                "new_password", "Password and confirmation password do not match."
            )

    old_password = forms.CharField(
        max_length=32, widget=forms.PasswordInput(attrs={"class": "form-control"})
    )

    new_password = forms.CharField(
        max_length=32, widget=forms.PasswordInput(attrs={"class": "form-control"})
    )

    new_password2 = forms.CharField(
        label="Password confirmation",
        max_length=32,
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
