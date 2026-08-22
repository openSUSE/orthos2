"""
This module contains the form used by superusers to create/edit any User account.
"""

from django import forms
from django.contrib.auth.models import User


class UserAdminForm(forms.ModelForm):  # type: ignore
    class Meta:  # type: ignore
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "is_staff",
            "is_superuser",
            "groups",
        ]
