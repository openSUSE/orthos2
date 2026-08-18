"""
Module which contains functionality related to the custom Serializer that is responsible for the "System" model.
"""

from typing import Dict

from rest_framework import serializers

from orthos2.data.models import System


class SystemSerializer(serializers.ModelSerializer[System]):
    class Meta:  # type: ignore
        model = System
        fields = (
            "id",
            "name",
            "virtual",
            "allowBMC",
            "allowHypervisor",
            "administrative",
        )

    @property
    def data_info(self) -> Dict[str, Dict[str, str]]:
        return self.data  # type: ignore
