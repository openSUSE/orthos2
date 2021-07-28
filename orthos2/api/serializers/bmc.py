from orthos2.data.models import BMC
from rest_framework import serializers


class BMCSerializer(serializers.ModelSerializer):

    class Meta:
        model = BMC
        exclude = [
            'machine'
        ]
