from orthos2.data.models import NetworkInterface
from rest_framework import serializers


class BMCSerializer(serializers.ModelSerializer):

    class Meta:
        model = BMC
        exclude = [
            'machine'
        ]