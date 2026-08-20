from django.test import TestCase

from orthos2.api.serializers.serialconsoletype import SerialConsoleTypeSerializer
from orthos2.data.models import SerialConsoleType


class SerialConsoleTypeSerializerTest(TestCase):
    """
    Verify that serial console type serialization is working as expected.
    """

    def test_serialization(self) -> None:
        """
        Verify that serial console type serialization is working as expected.
        """
        # Arrange
        serialconsoletype = SerialConsoleType.objects.create(name="AcmeConsole")
        serializer = SerialConsoleTypeSerializer(serialconsoletype)

        # Act
        result = serializer.data_info

        # Assert
        self.assertEqual(result["name"], "AcmeConsole")
