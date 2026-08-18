"""
Module which contains functionality related to the custom Serializer that is responsible for the `DomainAdmin`
model (the through-model of `Domain.supported_architectures`, exposed here as "domain architecture").
"""

from typing import Dict

from rest_framework import serializers

from orthos2.data.models import DomainAdmin


class DomainArchitectureSerializer(serializers.ModelSerializer[DomainAdmin]):
    class Meta:  # type: ignore
        model = DomainAdmin
        fields = ("id", "domain", "arch", "contact_email")

    @property
    def data_info(self) -> Dict[str, Dict[str, str]]:
        return self.data  # type: ignore
