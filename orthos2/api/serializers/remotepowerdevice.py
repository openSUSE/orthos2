"""
Module which contains functionality related to the custom Serializer that is responsible for the "Enclosure" model.
"""

from typing import Dict

from rest_framework import serializers

from orthos2.data.models import RemotePowerDevice


class RemotePowerDeviceSerializer(serializers.ModelSerializer[RemotePowerDevice]):
    class Meta:  # type: ignore
        model = RemotePowerDevice
        fields = (
            "fqdn",
            "id",
            "username",
            "mac",
            "url",
            "netbox_id",
            "netbox_last_fetch_attempt",
        )

    @property
    def data_info(self) -> Dict[str, Dict[str, str]]:
        return self.data  # type: ignore
