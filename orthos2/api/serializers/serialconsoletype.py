"""
Module which contains functionality related to the custom Serializer that is responsible for the "SerialConsoleType"
model.
"""

from typing import Dict

from rest_framework import serializers

from orthos2.data.models import SerialConsoleType


class SerialConsoleTypeSerializer(serializers.ModelSerializer[SerialConsoleType]):
    class Meta:  # type: ignore
        model = SerialConsoleType
        fields = ("id", "name", "command", "comment", "has_ipmi_sol")

    @property
    def data_info(self) -> Dict[str, Dict[str, str]]:
        return self.data  # type: ignore
