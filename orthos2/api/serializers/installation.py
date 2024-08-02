from rest_framework import serializers

from orthos2.data.models import Installation


class InstallationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Installation
        exclude = ["machine"]
