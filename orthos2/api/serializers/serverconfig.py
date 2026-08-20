"""
Module which contains functionality related to the custom Serializer that is responsible for the "ServerConfig"
model.
"""

from typing import Dict

from rest_framework import serializers

from orthos2.data.models import ServerConfig


class ServerConfigSerializer(serializers.ModelSerializer[ServerConfig]):
    class Meta:  # type: ignore
        model = ServerConfig
        fields = ("id", "key", "value")

    @property
    def data_info(self) -> Dict[str, Dict[str, str]]:
        return self.data  # type: ignore
