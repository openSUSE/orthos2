"""
Module which contains functionality related to the custom Serializer that is responsible for the "RemotePowerType"
model.
"""

from typing import Dict

from rest_framework import serializers

from orthos2.data.models import RemotePowerType


class RemotePowerTypeSerializer(serializers.ModelSerializer[RemotePowerType]):
    class Meta:  # type: ignore
        model = RemotePowerType
        fields = (
            "id",
            "name",
            "device",
            "username",
            "identity_file",
            "architectures",
            "systems",
            "use_port",
            "use_hostname_as_port",
        )

    @property
    def data_info(self) -> Dict[str, Dict[str, str]]:
        return self.data  # type: ignore
