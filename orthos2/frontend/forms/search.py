"""
This module contains the logic to allow a user to search for one or more machines.
"""

from typing import Dict, List, Tuple, Union

from django import forms

from orthos2.data.models import Installation, Machine, Platform, Vendor


def get_vendors() -> List[Tuple[str, str]]:
    vendors: List[Tuple[str, str]] = [("", "--all--")]
    for vendor in Vendor.objects.all().values("id", "name"):
        vendors.append((vendor["id"], vendor["name"]))  # type: ignore
    return vendors


def get_platforms() -> List[Tuple[str, Union[str, Tuple[Tuple[int, str], ...]]]]:
    platforms: List[Tuple[str, Union[str, Tuple[Tuple[int, str], ...]]]] = [
        ("", "--all--")
    ]
    groups: Dict[str, Tuple[Tuple[int, str], ...]] = {}
    for platform in Platform.objects.all():
        platform_id = platform.id
        name = platform.name
        platform_vendor = platform.vendor

        if platform.is_cartridge:
            continue

        if platform_vendor.name in groups.keys():
            groups[platform_vendor.name] += ((platform_id, name),)
        else:
            groups[platform_vendor.name] = ((platform_id, name),)

    for vendor, platforms_ in groups.items():
        platforms.append((vendor, platforms_))
    return platforms


def get_cartridge_platforms() -> List[
    Tuple[str, Union[str, Tuple[Tuple[int, str], ...]]]
]:
    platforms: List[Tuple[str, Union[str, Tuple[Tuple[int, str], ...]]]] = [
        ("", "--all--")
    ]
    groups: Dict[str, Tuple[Tuple[int, str], ...]] = {}
    for platform in Platform.objects.all():
        id = platform.id
        name = platform.name
        platform_vendor = platform.vendor

        if not platform.is_cartridge:
            continue

        if platform_vendor.name in groups.keys():
            groups[platform_vendor.name] += ((id, name),)
        else:
            groups[platform_vendor.name] = ((id, name),)

    for vendor, platforms_ in groups.items():
        platforms.append((vendor, platforms_))
    return platforms


def get_distributions() -> List[Tuple[str, str]]:
    installations = [("", "--all--")]
    for installation in Installation.objects.all().values("distribution").distinct():
        installations.append(
            (installation["distribution"], installation["distribution"])
        )
    return installations


def get_systems() -> List[Tuple[str, str]]:
    """Return system choices."""
    return Machine._meta.get_field("system").get_choices(blank_choice=[("", "--all--")])  # type: ignore


def get_architectures() -> List[Tuple[str, str]]:
    """Return architecture choices."""
    return Machine._meta.get_field("architecture").get_choices(  # type: ignore
        blank_choice=[("", "--all--")]
    )


class SearchForm(forms.Form):
    """
    Form to search for one or more machines.
    """

    def clean(self) -> None:
        cleaned_data = super(SearchForm, self).clean()
        if cleaned_data is None:
            # It may be that a superclass didn't return cleaned data (as this is optional)
            # https://docs.djangoproject.com/en/4.2/ref/forms/validation/#cleaning-and-validating-fields-that-depend-on-each-other
            cleaned_data = self.cleaned_data

        empty = True
        values = [
            value
            for key, value in cleaned_data.items()
            if not key.endswith("__operator")
        ]
        for value in values:
            if value:
                empty = False

        if empty:
            self.add_error(None, "Please provide at least one search parameter.")

        if cleaned_data["ram_amount"]:
            try:
                int(cleaned_data["ram_amount"])
            except ValueError:
                self.add_error("ram_amount", "Value must be a number.")

        if cleaned_data["cpu_cores"]:
            try:
                int(cleaned_data["cpu_cores"])
            except ValueError:
                self.add_error("cpu_cores", "Value must be a number.")

    enclosure__platform__vendor = forms.ChoiceField(
        required=False,
        choices=get_vendors,
        widget=forms.Select(attrs={"class": "custom-select form-control"}),
    )

    enclosure__platform = forms.ChoiceField(
        required=False,
        choices=get_platforms,
        widget=forms.Select(attrs={"class": "custom-select form-control"}),
    )

    platform = forms.ChoiceField(
        required=False,
        choices=get_cartridge_platforms,
        widget=forms.Select(attrs={"class": "custom-select form-control"}),
    )

    system = forms.ChoiceField(
        required=False,
        choices=get_systems,
        widget=forms.Select(attrs={"class": "custom-select form-control"}),
    )

    architecture = forms.ChoiceField(
        required=False,
        choices=get_architectures,
        widget=forms.Select(attrs={"class": "custom-select form-control"}),
    )

    fqdn = forms.CharField(
        required=False, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    fqdn__operator = forms.CharField(initial="__icontains", widget=forms.HiddenInput())

    cpu_model = forms.CharField(
        required=False, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    cpu_model__operator = forms.CharField(
        initial="__icontains", widget=forms.HiddenInput()
    )

    cpu_flags = forms.CharField(
        required=False, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    cpu_flags__operator = forms.CharField(
        initial="__icontains", widget=forms.HiddenInput()
    )

    ram_amount = forms.DecimalField(
        required=False,
        min_value=1,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    ram_amount__operator = forms.ChoiceField(
        choices=(("__gt", ">"), ("__exact", "="), ("__lt", "<")),
        required=False,
        initial="__gt",
        widget=forms.RadioSelect(attrs={"autocomplete": "off"}),
    )

    cpu_cores = forms.DecimalField(
        required=False,
        min_value=1,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    cpu_cores__operator = forms.ChoiceField(
        choices=(("__gt", ">"), ("__exact", "="), ("__lt", "<")),
        required=False,
        initial="__gt",
        widget=forms.RadioSelect(attrs={"autocomplete": "off"}),
    )

    hwinfo = forms.CharField(
        required=False, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    hwinfo__operator = forms.CharField(
        initial="__icontains", widget=forms.HiddenInput()
    )

    dmidecode = forms.CharField(
        required=False, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    dmidecode__operator = forms.CharField(
        initial="__icontains", widget=forms.HiddenInput()
    )

    dmesg = forms.CharField(
        required=False, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    dmesg__operator = forms.CharField(initial="__icontains", widget=forms.HiddenInput())

    lspci = forms.CharField(
        required=False, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    lspci__operator = forms.CharField(initial="__icontains", widget=forms.HiddenInput())

    lsmod = forms.CharField(
        required=False, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    lsmod__operator = forms.CharField(initial="__icontains", widget=forms.HiddenInput())

    installations__distribution = forms.ChoiceField(
        required=False,
        choices=(get_distributions),
        widget=forms.Select(attrs={"class": "custom-select form-control"}),
    )

    reserved_by = forms.ChoiceField(
        required=False,
        choices=(("__False", "yes"), ("__True", "no"), ("", "not relevant")),
        widget=forms.RadioSelect(attrs={"autocomplete": "off"}),
    )
    reserved_by__operator = forms.CharField(
        initial="__isnull", widget=forms.HiddenInput()
    )

    ipmi = forms.ChoiceField(
        required=False,
        choices=(("__True", "yes"), ("__False", "no"), ("", "not relevant")),
        widget=forms.RadioSelect(attrs={"autocomplete": "off"}),
    )

    efi = forms.ChoiceField(
        required=False,
        choices=(("__True", "yes"), ("__False", "no"), ("", "not relevant")),
        widget=forms.RadioSelect(attrs={"autocomplete": "off"}),
    )

    networkinterfaces__mac_address = forms.CharField(
        required=False, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    networkinterfaces__mac_address__operator = forms.CharField(
        initial="__icontains", widget=forms.HiddenInput()
    )

    serialconsole = forms.ChoiceField(
        required=False,
        choices=(("__False", "yes"), ("__True", "no"), ("", "not relevant")),
        widget=forms.RadioSelect(attrs={"autocomplete": "off"}),
    )
    serialconsole__operator = forms.CharField(
        initial="__isnull", widget=forms.HiddenInput()
    )

    remotepower = forms.ChoiceField(
        required=False,
        choices=(("__False", "yes"), ("__True", "no"), ("", "not relevant")),
        widget=forms.RadioSelect(attrs={"autocomplete": "off"}),
    )
    remotepower__operator = forms.CharField(
        initial="__isnull", widget=forms.HiddenInput()
    )

    status_ipv4 = forms.ChoiceField(
        required=False,
        choices=Machine._meta.get_field("status_ipv4").get_choices(  # type: ignore
            blank_choice=[("", "Not relevant")]
        ),
        widget=forms.Select(attrs={"class": "custom-select form-control"}),
    )

    status_ipv6 = forms.ChoiceField(
        required=False,
        choices=Machine._meta.get_field("status_ipv6").get_choices(  # type: ignore
            blank_choice=[("", "Not relevant")]
        ),
        widget=forms.Select(attrs={"class": "custom-select form-control"}),
    )

    status_ssh = forms.ChoiceField(
        required=False,
        choices=(("__True", "yes"), ("__False", "no"), ("", "not relevant")),
        widget=forms.RadioSelect(attrs={"autocomplete": "off"}),
    )

    status_login = forms.ChoiceField(
        required=False,
        choices=(("__True", "yes"), ("__False", "no"), ("", "not relevant")),
        widget=forms.RadioSelect(attrs={"autocomplete": "off"}),
    )
