from typing import Any, Dict

from django import forms
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import IntegrityError
from django.forms import BaseForm
from django.http import HttpResponse
from django.urls import reverse
from django.views.generic.edit import FormView
from requests import HTTPError

from orthos2.data.models import Architecture, Enclosure, Machine, System
from orthos2.utils.netbox import Netbox


def safe_fetch_device(netbox_api: Netbox, netbox_id: str) -> Dict[str, Any]:
    try:
        result = netbox_api.fetch_device(int(netbox_id))
    except HTTPError as e:
        if e.response.status_code == 404:
            return {}
        raise e
    return result


def safe_fetch_vm(netbox_api: Netbox, netbox_id: str) -> Dict[str, Any]:
    try:
        result = netbox_api.fetch_vm(int(netbox_id))
    except HTTPError as e:
        if e.response.status_code == 404:
            return {}
        raise e
    return result


class AddMachineForm(forms.Form):
    netbox_id = forms.CharField(
        required=True,
        label="NetBox ID",
        help_text="The ID that NetBox gives to the object.",
    )
    system = forms.ModelChoiceField(
        queryset=System.objects.all(),
        required=True,
        help_text="The system type the NetBox machine belongs to. In case the given NetBox ID is for an enclosure, "
        "this field is ignored.",
    )
    netbox_object_type = forms.ChoiceField(
        choices=[
            ("device", "Device"),
            ("vm", "Virtual Machine"),
        ],
        required=True,
        label="NetBox Object Type",
        help_text="The type of the NetBox object to be added. This is used to determine if the NetBox ID refers to a "
        "Device or a Virtual Machine.",
    )

    def clean(self) -> None:
        """
        Verify that a single Device or VM in NetBox exists with the given ID.
        """
        if not self.is_valid():
            return
        netbox_api = Netbox.get_instance()
        if self.cleaned_data["netbox_object_type"] == "device":
            netbox_obj = safe_fetch_device(netbox_api, self.cleaned_data["netbox_id"])
            if not netbox_obj:
                self.add_error("netbox_id", "No NetBox Device found with the given ID.")
                return
        elif self.cleaned_data["netbox_object_type"] == "vm":
            netbox_obj = safe_fetch_vm(netbox_api, self.cleaned_data["netbox_id"])
            if not netbox_obj:
                self.add_error(
                    "netbox_id", "No NetBox Virtual Machine found with the given ID."
                )
                return


class AddMachineFormView(FormView):
    template_name = "frontend/machines/add.html"
    form_class = AddMachineForm

    def __init__(self, **kwargs):
        super(AddMachineFormView, self).__init__(**kwargs)
        self.__machine_pk = 0

    def get_context_data(self, **kwargs):
        context = super(AddMachineFormView, self).get_context_data(**kwargs)
        context["title"] = "Add Machine"
        return context

    def form_valid(self, form: BaseForm) -> HttpResponse:
        netbox_api = Netbox.get_instance()
        netbox_object_type = form.data["netbox_object_type"]
        if netbox_object_type == "device":
            netbox_object = safe_fetch_device(netbox_api, form.data["netbox_id"])
            object_name = netbox_object.get("name", "")
            # Try existing enclosure
            try:
                existing_enclosure = Enclosure.objects.get(name=object_name)
                existing_enclosure.netbox_id = form.data["netbox_id"]
                existing_enclosure.save()
                return super().form_valid(form)
            except ObjectDoesNotExist:
                # Try next objects type
                pass
        else:
            netbox_object = safe_fetch_vm(netbox_api, form.data["netbox_id"])
            object_name = netbox_object.get("name", "")
        # Try existing machine
        try:
            existing_machine = Machine.objects.get(fqdn=object_name)
            existing_machine.netbox_id = form.data["netbox_id"]
            existing_machine.save()
            self.__machine_pk = existing_machine.pk
            return super().form_valid(form)
        except ObjectDoesNotExist:
            # Try next object type
            pass
        # Create new machine
        machine_arch = netbox_object.get("custom_fields", {}).get("arch")
        if machine_arch is None:
            form.add_error(
                "netbox_id",
                "Machine or VM doesn't have a CPU Architecture set in NetBox.",
            )
            return super().form_invalid(form)
        try:
            target_arch = Architecture.objects.get(name=machine_arch)
        except ObjectDoesNotExist:
            form.add_error(
                "netbox_id",
                "Machine architecture couldn't be found in Orthos 2 or not set in NetBox.",
            )
            return super().form_invalid(form)
        new_machine = Machine()
        new_machine.fqdn = object_name
        new_machine.architecture = target_arch
        new_machine.system_id = form.data["system"]
        new_machine.netbox_id = form.data["netbox_id"]
        try:
            new_machine.save()
        except ValidationError as e:
            form.add_error("netbox_id", e)
            return super().form_invalid(form)
        except IntegrityError as e:
            form.add_error("netbox_id", str(e))
            return super().form_invalid(form)
        return super().form_valid(form)

    def get_success_url(self):
        if self.__machine_pk > 0:
            return reverse("frontend:detail", args=[self.__machine_pk])
        return reverse("frontend:machines")
