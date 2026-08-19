"""
Module which contains functionality related to the custom Serializer that is responsible for the "DeviceType" model.
"""

from typing import Dict

from rest_framework import serializers

from orthos2.data.models import DeviceType


class DeviceTypeSerializer(serializers.ModelSerializer[DeviceType]):
    class Meta:  # type: ignore
        model = DeviceType
        fields = ("id", "name", "manufacturer", "is_cartridge", "description")

    @property
    def data_info(self) -> Dict[str, Dict[str, str]]:
        return self.data  # type: ignore
