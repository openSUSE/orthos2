from rest_framework import serializers

from data.models import Installation


class InstallationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Installation
        exclude = [
            'machine'
        ]
