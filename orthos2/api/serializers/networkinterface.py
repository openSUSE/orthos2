from rest_framework import serializers

from data.models import NetworkInterface


class NetworkInterfaceSerializer(serializers.ModelSerializer):

    class Meta:
        model = NetworkInterface
        exclude = [
            'machine'
        ]
