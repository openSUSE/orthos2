from orthos2.data.models import Annotation
from rest_framework import serializers


class AnnotationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Annotation
        exclude = [
            'machine'
        ]
