"""
Module which contains functionality related to the custom Serializer that is responsible for the "Manufacturer" model.
"""

from typing import Dict

from rest_framework import serializers

from orthos2.data.models import Manufacturer


class ManufacturerSerializer(serializers.ModelSerializer[Manufacturer]):
    class Meta:  # type: ignore
        model = Manufacturer
        fields = ("id", "name")

    @property
    def data_info(self) -> Dict[str, Dict[str, str]]:
        return self.data  # type: ignore
