"""
Module which contains functionality related to the custom Serializer that is responsible for the "SingleTask" model.
"""

from typing import Dict

from rest_framework import serializers

from orthos2.taskmanager.models import SingleTask


class SingleTaskSerializer(serializers.ModelSerializer[SingleTask]):
    class Meta:  # type: ignore
        model = SingleTask
        fields = (
            "id",
            "name",
            "module",
            "arguments",
            "priority",
            "hash",
            "running",
            "created",
        )

    @property
    def data_info(self) -> Dict[str, Dict[str, str]]:
        return self.data  # type: ignore
