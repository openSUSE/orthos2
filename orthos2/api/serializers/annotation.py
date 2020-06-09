from rest_framework import serializers

from data.models import Annotation


class AnnotationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Annotation
        exclude = [
            'machine'
        ]
