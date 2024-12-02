from rest_framework import serializers

from orthos2.data.models import Installation


class InstallationSerializer(serializers.ModelSerializer[Installation]):
    class Meta:  # type: ignore
        model = Installation
        exclude = ["machine"]
