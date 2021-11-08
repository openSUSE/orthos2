from rest_framework import serializers

from orthos2.data.models import Annotation


class AnnotationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Annotation
        exclude = [
            'machine'
        ]
