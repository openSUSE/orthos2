"""
This module contains the form used to create/edit a Group.
"""

from django import forms
from django.contrib.auth.models import Group


class GroupForm(forms.ModelForm):  # type: ignore
    class Meta:  # type: ignore
        model = Group
        fields = ["name", "permissions"]
