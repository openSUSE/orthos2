from rest_framework import serializers

from orthos2.data.models import NetworkInterface


class NetworkInterfaceSerializer(serializers.ModelSerializer[NetworkInterface]):
    class Meta:  # type: ignore
        model = NetworkInterface
        exclude = ["machine"]
