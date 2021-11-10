from rest_framework import serializers

from orthos2.data.models import NetworkInterface


class NetworkInterfaceSerializer(serializers.ModelSerializer):

    class Meta:
        model = NetworkInterface
        exclude = [
            'machine'
        ]
