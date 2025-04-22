from typing import Any, Dict

from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.views.generic.edit import FormView
from requests import HTTPError

from orthos2.data.models import Enclosure, Machine, System, Architecture
from orthos2.utils.netbox import Netbox


def safe_fetch_device(netbox_api: Netbox, netbox_id: str) -> Dict[str, Any]:
    try:
        result = netbox_api.fetch_device(netbox_id)
    except HTTPError as e:
        if e.response.status_code == 404:
            return {}
        raise e
    return result


def safe_fetch_vm(netbox_api: Netbox, netbox_id: str) -> Dict[str, Any]:
    try:
        result = netbox_api.fetch_vm(netbox_id)
    except HTTPError as e:
        if e.response.status_code == 404:
            return {}
        raise e
    return result


class AddMachineForm(forms.Form):
    netbox_id = forms.CharField(required=True, label="NetBox ID", help_text="The ID that NetBox gives to the object.")
    system = forms.ModelChoiceField(
        queryset=System.objects.all(),
        required=True,
        help_text="The system type the NetBox machine belongs to. In case the given NetBox ID is for an enclosure, this field is ignored.",
    )

    def clean(self):
        """
        Verify that a single Device or VM in NetBox exists with the given ID.
        """
        if not self.is_valid():
            return
        netbox_api = Netbox.get_instance()
        netbox_device = safe_fetch_device(netbox_api, self.cleaned_data["netbox_id"])
        netbox_vm = safe_fetch_vm(netbox_api, self.cleaned_data["netbox_id"])
        device_found = len(netbox_device) > 0
        vm_found = len(netbox_vm) > 0
        if not device_found and not vm_found:
            self.add_error("netbox_id", "Found neither a NetBox Device nor a NetBox VM.")
            return
        if self.cleaned_data["system"].name == "BareMetal" and (not device_found or vm_found):
            self.add_error("netbox_id", "NetBox ID matched a virtual machine or didn't match a device.")


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

    def form_valid(self, form):
        netbox_api = Netbox.get_instance()
        netbox_device = safe_fetch_device(netbox_api, form.data["netbox_id"])
        device_name = netbox_device.get("name", "")
        netbox_vm = safe_fetch_vm(netbox_api, form.data["netbox_id"])
        vm_name = netbox_vm.get("name", "")
        if device_name:
            # Try existing enclosure
            try:
                existing_enclosure = Enclosure.objects.get(name=device_name)
                existing_enclosure.netbox_id = form.data["netbox_id"]
                existing_enclosure.save()
                return super().form_valid(form)
            except ObjectDoesNotExist:
                # Try next objects type
                pass
        if vm_name or device_name:
            # Try existing machine
            try:
                existing_machine = Machine.objects.get(fqdn=device_name)
                existing_machine.netbox_id = form.data["netbox_id"]
                existing_machine.save()
                self.__machine_pk = existing_machine.pk
                return super().form_valid(form)
            except ObjectDoesNotExist:
                # Try next object type
                pass
            # Create new machine
            machine_name = device_name if device_name else vm_name
            machine_arch = netbox_device.get("custom_fields", {}).get("arch") if device_name else netbox_vm.get("custom_fields", {}).get("arch")
            if machine_name is None:
                form.add_error("netbox_id", "Machine or VM doesn't have a CPU Architecture set in NetBox.")
                return super().form_invalid(form)
            new_machine = Machine()
            new_machine.fqdn = machine_name
            new_machine.architecture = Architecture.objects.get(name=machine_arch)
            new_machine.system = form.data["system"]
            new_machine.netbox_id = form.data["netbox_id"]
            new_machine.save()
        return super().form_valid(form)

    def get_success_url(self):
        if self.__machine_pk > 0:
            return reverse("frontend:detail", args=[self.__machine_pk])
        return reverse("frontend:machines")
