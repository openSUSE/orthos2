import datetime
from typing import TYPE_CHECKING, Any, Dict, List

from django.utils import timezone
from rest_framework import serializers

from orthos2.api.serializers.annotation import AnnotationSerializer
from orthos2.api.serializers.bmc import BMCSerializer
from orthos2.api.serializers.installation import InstallationSerializer
from orthos2.api.serializers.networkinterface import NetworkInterfaceSerializer
from orthos2.data.models import Machine

if TYPE_CHECKING:
    from orthos2.data.models.annotation import Annotation
    from orthos2.data.models.bmc import BMC
    from orthos2.data.models.installation import Installation
    from orthos2.data.models.networkinterface import NetworkInterface


class NetworkInterfaceListingField(NetworkInterfaceSerializer):
    def to_representation(
        self, instance: "NetworkInterface"
    ) -> Dict[str, Dict[str, Any]]:
        result: Dict[str, Dict[str, Any]] = {}

        for name, field in self.fields.items():  # type: ignore
            value = getattr(instance, name)
            result[name] = {"label": field.label, "value": value}

        return result


class InstallationListingField(InstallationSerializer):
    def to_representation(self, instance: "Installation") -> Dict[str, Dict[str, Any]]:
        result: Dict[str, Dict[str, Any]] = {}

        for name, field in self.fields.items():  # type: ignore
            value = getattr(instance, name)
            result[name] = {"label": field.label, "value": value}

        return result


class AnnotationListingField(AnnotationSerializer):
    def to_representation(self, instance: "Annotation") -> Dict[str, Dict[str, Any]]:
        result: Dict[str, Dict[str, Any]] = {}

        for name, field in self.fields.items():  # type: ignore
            value = getattr(instance, str(name))
            if name == "reporter":
                if value:
                    value = value.username
                else:
                    value = "unknown"
            result[name] = {"label": field.label, "value": value}

        return result


class BMCListingField(BMCSerializer):
    def to_representation(self, instance: "BMC") -> Dict[str, Dict[str, Any]]:
        result: Dict[str, Dict[str, Any]] = {}

        for name, field in self.fields.items():  # type: ignore
            value = getattr(instance, str(name))
            result[name] = {"label": field.label, "value": value}
        return result


class DateTimeInfiniteField(serializers.DateTimeField):
    def to_representation(self, value: "datetime.datetime") -> str:
        if value.date() == datetime.date.max:
            current_time_offset = datetime.datetime.now(
                tz=timezone.get_current_timezone()
            ).utcoffset()
            if current_time_offset is None:
                raise RuntimeError("Timezone could not be determined!")
            custom_max = (
                datetime.datetime.combine(
                    datetime.date.max, datetime.time.max, tzinfo=datetime.timezone.utc
                )
                - current_time_offset
            )
            return super().to_representation(custom_max)
        return super().to_representation(value)


class MachineSerializer(serializers.ModelSerializer[Machine]):

    enclosure = serializers.StringRelatedField()  # type: ignore

    system = serializers.StringRelatedField()  # type: ignore

    architecture = serializers.StringRelatedField()  # type: ignore

    networkinterfaces = NetworkInterfaceListingField(many=True)

    reserved_by = serializers.StringRelatedField()  # type: ignore
    reserved_until = DateTimeInfiniteField()

    installations = InstallationListingField(many=True)

    annotations = AnnotationListingField(many=True)

    status_ipv4 = serializers.SerializerMethodField()
    status_ipv6 = serializers.SerializerMethodField()
    bmc = BMCListingField()

    class Meta:  # type: ignore
        model = Machine
        fields = (
            "fqdn",
            "id",
            "ip_address_v4",
            "ip_address_v6",
            "comment",
            "group",
            "serial_number",
            "product_code",
            "enclosure",
            "nda",
            "system",
            "bmc",
            "bmc_fqdn",
            "bmc_mac",
            "bmc_password",
            "bmc_username",
            "architecture",
            "networkinterfaces",
            "installations",
            "annotations",
            "status_ipv6",
            "status_ipv4",
            "status_ssh",
            "status_login",
            "reserved_by",
            "reserved_reason",
            "reserved_at",
            "reserved_until",
            "cpu_model",
            "cpu_id",
            "cpu_cores",
            "cpu_physical",
            "cpu_threads",
            "cpu_flags",
            "ram_amount",
            "serial_type",
            "serial_console_server",
            "serial_port",
            "serial_command",
            "serial_comment",
            "serial_baud_rate",
            "serial_kernel_device",
            "serial_kernel_device_num",
            "power_type",
            "power_host",
            "power_port",
            "power_comment",
            "location_room",
            "location_rack",
            "location_rack_position",
        )

    serial_type = serializers.CharField(source="serialconsole.stype.name")

    serial_console_server = serializers.CharField(source="serialconsole.console_server")
    serial_port = serializers.IntegerField(source="serialconsole.port")
    serial_command = serializers.CharField(source="serialconsole.command")
    serial_comment = serializers.CharField(source="serialconsole.comment")
    serial_baud_rate = serializers.IntegerField(source="serialconsole.baud_rate")
    serial_kernel_device = serializers.CharField(source="serialconsole.kernel_device")
    serial_kernel_device_num = serializers.IntegerField(
        source="serialconsole.kernel_device_num"
    )

    power_type = serializers.CharField(source="remotepower.fence_name")

    power_host = serializers.CharField(source="remotepower.remote_power_device")
    power_port = serializers.CharField(source="remotepower.port")
    power_comment = serializers.CharField(source="remotepower.comment")

    bmc_fqdn = serializers.CharField(source="bmc.fqdn")
    bmc_mac = serializers.CharField(source="bmc.mac")
    bmc_username = serializers.CharField(source="bmc.username")
    bmc_password = serializers.SerializerMethodField()

    def get_bmc_password(self, obj: Any) -> str:
        if hasattr(self, "bmc") and self.bmc:
            if self.bmc_password:
                return "***"
        return "-"

    location_room = serializers.CharField(source="enclosure.location_room")
    location_rack = serializers.CharField(source="enclosure.location_rack")
    location_rack_position = serializers.CharField(
        source="enclosure.location_rack_position"
    )

    group = serializers.CharField(source="group.name")

    def __init__(self, machine: Machine, *args: Any, **kwargs: Any) -> None:
        super(MachineSerializer, self).__init__(machine, *args, **kwargs)
        if not hasattr(machine, "group") or not machine.group:
            self.fields.pop("group")  # type: ignore

    @property
    def data_info(self) -> Dict[str, Dict[str, str]]:
        result: Dict[str, Dict[str, str]] = {}

        # copy dictionary for further manipulation
        data = self.data  # type: ignore

        # add keys to exclude list which shouldn't be displayed if value is empty...
        exclude: List[str] = []
        for key in self.fields.keys():
            if key.startswith("serial_") or key.startswith("power_"):
                exclude.append(key)

        exclude.remove("serial_type")
        exclude.remove("power_type")

        for name, field in self.fields.items():  # type: ignore
            if name == "ip_address_v4":
                field.label = "IPv4"
            if name == "ip_address_v6":
                field.label = "IPv6"
            if name == "status_ipv4":
                field.label = "Status IPv4"
            if name == "status_ipv6":
                field.label = "Status IPv6"
            # TODO: Adapt this to the new implementation
            # if name == 'power_type' and data[name]:
            #    data[name] = RemotePower.Type.to_str(data[name])
            # ... do not add label/values if in exclude list
            if (name in exclude) and (data[name] is None):
                continue

            result[name] = {"label": field.label, "value": data[name]}  # type: ignore

        return result

    def get_status_ipv4(self, obj: "Machine") -> str:
        """
        Dynamically called method by SerializerMethodField of ``status_ipv4``.

        :param obj: The machine to be serialized.
        :returns: The string representation of the enum value.
        """
        # get_FOO_display() is a magic method of choice model fields.
        return obj.get_status_ipv4_display()  # type: ignore

    def get_status_ipv6(self, obj: "Machine") -> str:
        """
        Dynamically called method by SerializerMethodField of ``status_ipv4``.

        :param obj: The machine to be serialized.
        :returns: The string representation of the enum value.
        """
        # get_FOO_display() is a magic method of choice model fields.
        return obj.get_status_ipv6_display()  # type: ignore
