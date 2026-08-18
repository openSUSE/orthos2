from django.test import TestCase

from orthos2.api.serializers.singletask import SingleTaskSerializer
from orthos2.taskmanager.models import SingleTask


class SingleTaskSerializerTest(TestCase):
    """
    Verify that single task serialization is working as expected.
    """

    def test_serialization(self) -> None:
        """
        Verify that single task serialization is working as expected.
        """
        # Arrange
        singletask = SingleTask.objects.create(
            name="AcmeTask", module="acme.module", arguments="[[], {}]"
        )
        serializer = SingleTaskSerializer(singletask)

        # Act
        result = serializer.data_info

        # Assert
        self.assertEqual(result["name"], "AcmeTask")
