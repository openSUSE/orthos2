"""
Module which contains functionality related to the custom Serializer that is responsible for the "Vendor" model.
"""

from typing import Dict

from rest_framework import serializers

from orthos2.data.models import Vendor


class VendorSerializer(serializers.ModelSerializer[Vendor]):
    class Meta:  # type: ignore
        model = Vendor
        fields = ("id", "name")

    @property
    def data_info(self) -> Dict[str, Dict[str, str]]:
        return self.data  # type: ignore
