"""
This module contains the logic to help adding a new user with the built-in authentication provider.
"""

from typing import Any, Dict, Optional

from django import forms
from django.conf import settings
from django.contrib.auth.models import User

from orthos2.data.models import ServerConfig


class NewUserForm(forms.Form):
    """
    Form to add a new user with the built-in authentication provider.
    """

    login = forms.CharField(
        max_length=100, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    password = forms.CharField(
        max_length=32, widget=forms.PasswordInput(attrs={"class": "form-control"})
    )
    password2 = forms.CharField(
        label="Password confirmation",
        max_length=32,
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    email = forms.EmailField(
        max_length=64, widget=forms.TextInput(attrs={"class": "form-control"})
    )

    def clean(self) -> Optional[Dict[str, Any]]:
        cleaned_data = super(NewUserForm, self).clean()
        if cleaned_data is None:
            # It may be that a superclass didn't return cleaned data (as this is optional)
            # https://docs.djangoproject.com/en/4.2/ref/forms/validation/#cleaning-and-validating-fields-that-depend-on-each-other
            cleaned_data = self.cleaned_data

        login = cleaned_data.get("login")
        password = cleaned_data.get("password")
        password2 = cleaned_data.get("password2")
        email = cleaned_data.get("email")

        if User.objects.filter(username=login).count() > 0:
            self.add_error("login", "User '{}' does already exist.".format(login))

        if len(password) < 8:  # type: ignore
            self.add_error(
                "password",
                "Password is too short. It must contain at least 8 characters.",
            )

        if password != password2:
            self.add_error(
                "password", "Password and confirmation password do not match."
            )

        if email:
            valid_domains = ServerConfig.objects.list_by_key("mail.validdomains")

            if valid_domains is None:
                self.add_error(
                    None,
                    "Please contact support ({}).".format(settings.SUPPORT_CONTACT),
                )
            elif valid_domains and (email.split("@")[1] not in valid_domains):
                self.add_error(
                    "email",
                    "Please use a valid email domain: {}".format(
                        ", ".join(valid_domains)
                    ),
                )

            if User.objects.filter(email__icontains=email).count():
                self.add_error(
                    "email", "Email address '{}' is already in use.".format(email)
                )
        return None
