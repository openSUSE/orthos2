from rest_framework import serializers

from orthos2.data.models import BMC


class BMCSerializer(serializers.ModelSerializer):
    class Meta:
        model = BMC
        exclude = ["machine"]
