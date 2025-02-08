from typing import Any, List, Union

from django.http import HttpResponseRedirect, JsonResponse
from django.urls import URLPattern, re_path
from rest_framework.request import Request

from orthos2.api.commands.base import BaseAPIView, get_machine, getException
from orthos2.api.serializers.machine import MachineSerializer
from orthos2.api.serializers.misc import ErrorMessage, Serializer
from orthos2.data.models import Machine


class InfoCommand(BaseAPIView):

    METHOD = "GET"
    URL = "/machine"
    ARGUMENTS = (["fqdn"],)

    HELP_SHORT = "Retrieve information about a machine."
    HELP = """Command to get information about a machine.

Usage:
    INFO <fqdn>

Arguments:
    fqdn - FQDN or hostname of the machine.

Example:
    INFO foo.domain.tld
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(r"^machine$", InfoCommand.as_view(), name="machine"),
        ]

    @staticmethod
    def get_tabcompletion() -> List[str]:
        return list(Machine.api.all().values_list("fqdn", flat=True))

    def get(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> Union[JsonResponse, HttpResponseRedirect]:
        """Return machine information."""
        fqdn = request.GET.get("fqdn", "")
        response = {}

        try:
            result = get_machine(fqdn, redirect_to="api:machine", data=request.GET)
            if isinstance(result, Serializer):
                return result.as_json
            elif isinstance(result, HttpResponseRedirect):
                return result
            machine = result

            machine.enclosure.fetch_location(machine.pk)
            serialzed_machine = MachineSerializer(machine)

            order = [
                "fqdn",
                "id",
                "architecture",
                "ipv4",
                "ipv6",
                "serial_number",
                "product_code",
                "comment",
                "nda",
                None,
                "system",
                "enclosure",
                "group",
                None,
                "location_room",
                "location_rack",
                "location_rack_position",
                None,
                "reserved_by",
                "reserved_reason",
                "reserved_at",
                "reserved_until",
                None,
                "status_ipv4",
                "status_ipv6",
                "status_ssh",
                "status_login",
                None,
                "cpu_model",
                "cpu_id",
                "cpu_physical",
                "cpu_cores",
                "cpu_threads",
                "cpu_flags",
                "ram_amount",
                None,
                "serial_type",
                "serial_cscreen_server",
                "serial_console_server",
                "serial_port",
                "serial_command",
                "serial_comment",
                "serial_baud_rate",
                "serial_kernel_device",
                "serial_kernel_device_num",
                None,
                "power_type",
                "power_host",
                "power_port",
                "power_device",
                "power_comment",
                None,
                "bmc_fqdn",
                "bmc_mac",
                "bmc_username",
                "bmc_password",
                [
                    "installations",
                    [
                        "distribution",
                        "active",
                        "partition",
                        "architecture",
                        "kernelversion",
                    ],
                ],
                [
                    "networkinterfaces",
                    [
                        "mac_address",
                        "name",
                        "ethernet_type",
                        "driver_module",
                        "primary",
                    ],
                ],
                ["annotations", ["text", "reporter", "created"]],
            ]

            response["header"] = {"type": "INFO", "order": order}
            response["data"] = serialzed_machine.data_info  # type: ignore
        except Exception:
            return ErrorMessage(getException()).as_json

        return JsonResponse(response)
