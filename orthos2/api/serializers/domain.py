"""
Module which contains functionality related to the custom Serializer that is responsible for the "Domain" model.
"""

from typing import Dict

from rest_framework import serializers

from orthos2.data.models import Domain


class DomainSerializer(serializers.ModelSerializer[Domain]):
    class Meta:  # type: ignore
        model = Domain
        fields = (
            "id",
            "name",
            "cobbler_server",
            "cobbler_server_username",
            "tftp_server",
            "cscreen_server",
            "ip_v4",
            "ip_v6",
            "subnet_mask_v4",
            "subnet_mask_v6",
            "enable_v4",
            "enable_v6",
            "dynamic_range_v4_start",
            "dynamic_range_v4_end",
            "dynamic_range_v6_start",
            "dynamic_range_v6_end",
        )

    @property
    def data_info(self) -> Dict[str, Dict[str, str]]:
        return self.data  # type: ignore
