from rest_framework import serializers

from orthos2.data.models import Annotation


class AnnotationSerializer(serializers.ModelSerializer[Annotation]):
    class Meta:  # type: ignore
        model = Annotation
        exclude = ["machine"]
