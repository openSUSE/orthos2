"""
Module which contains functionality related to the custom Serializer that is responsible for the "Architecture"
model.
"""

from typing import Dict

from rest_framework import serializers

from orthos2.data.models import Architecture


class ArchitectureSerializer(serializers.ModelSerializer[Architecture]):
    class Meta:  # type: ignore
        model = Architecture
        fields = (
            "id",
            "name",
            "dhcp_filename",
            "contact_email",
            "default_profile",
        )

    @property
    def data_info(self) -> Dict[str, Dict[str, str]]:
        return self.data  # type: ignore
