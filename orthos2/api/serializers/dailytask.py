"""
Module which contains functionality related to the custom Serializer that is responsible for the "DailyTask" model.
"""

from typing import Dict

from rest_framework import serializers

from orthos2.taskmanager.models import DailyTask


class DailyTaskSerializer(serializers.ModelSerializer[DailyTask]):
    class Meta:  # type: ignore
        model = DailyTask
        fields = (
            "id",
            "name",
            "module",
            "arguments",
            "priority",
            "enabled",
            "executed_at",
            "hash",
            "running",
            "created",
        )

    @property
    def data_info(self) -> Dict[str, Dict[str, str]]:
        return self.data  # type: ignore
