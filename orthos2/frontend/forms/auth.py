from django import forms
from django.contrib.auth.forms import AuthenticationForm


class RememberUsernameAuthenticationForm(AuthenticationForm):
    """Authentication form with 'Remember username' checkbox."""

    remember_username = forms.BooleanField(
        required=False,
        initial=False,
        label="Remember username",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    def __init__(self, request=None, *args, **kwargs):
        # Pre-fill username from cookie if present
        if request and request.COOKIES.get("orthos2_remembered_username"):
            initial_username = request.COOKIES.get("orthos2_remembered_username")
            if "initial" not in kwargs:
                kwargs["initial"] = {}
            kwargs["initial"]["username"] = initial_username
            kwargs["initial"]["remember_username"] = True

        super().__init__(request, *args, **kwargs)
