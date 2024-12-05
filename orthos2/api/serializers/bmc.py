from rest_framework import serializers

from orthos2.data.models import BMC


class BMCSerializer(serializers.ModelSerializer[BMC]):
    class Meta:  # type: ignore
        model = BMC
        exclude = ["machine"]
