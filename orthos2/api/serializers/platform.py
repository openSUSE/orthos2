"""
Module which contains functionality related to the custom Serializer that is responsible for the "Platform" model.
"""

from typing import Dict

from rest_framework import serializers

from orthos2.data.models import Platform


class PlatformSerializer(serializers.ModelSerializer[Platform]):
    class Meta:  # type: ignore
        model = Platform
        fields = ("id", "name", "manufacturer", "is_cartridge", "description")

    @property
    def data_info(self) -> Dict[str, Dict[str, str]]:
        return self.data  # type: ignore
