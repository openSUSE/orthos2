from orthos2.data.models import Installation
from rest_framework import serializers


class InstallationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Installation
        exclude = [
            'machine'
        ]
