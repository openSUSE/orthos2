from orthos2.data.models import NetworkInterface
from rest_framework import serializers


class NetworkInterfaceSerializer(serializers.ModelSerializer):

    class Meta:
        model = NetworkInterface
        exclude = [
            'machine'
        ]
