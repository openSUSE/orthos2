"""
Module which contains functionality related to the custom Serializer that is responsible for the "Enclosure" model.
"""

from typing import Dict

from rest_framework import serializers

from orthos2.data.models.enclosure import Enclosure


class EnclosureSerializer(serializers.ModelSerializer[Enclosure]):
    class Meta:  # type: ignore
        model = Enclosure
        fields = (
            "name",
            "id",
            "description",
            "netbox_id",
            "platform",
            "netbox_last_fetch_attempt",
            "location_site",
            "location_room",
            "location_rack",
            "location_rack_position",
        )

    @property
    def data_info(self) -> Dict[str, Dict[str, str]]:
        return self.data  # type: ignore
