from django.test import TestCase

from orthos2.api.serializers.enclosure import EnclosureSerializer
from orthos2.data.models import Enclosure


class EnclosureSerializerTest(TestCase):
    """
    Verify that enclosure serialization is working as expected.
    """

    def test_serialization(self) -> None:
        """
        Verify that enclosure serialization is working as expected.
        """
        # Arrange
        enclosure = Enclosure.objects.create(name="AcmeEnclosure")
        serializer = EnclosureSerializer(enclosure)

        # Act
        result = serializer.data_info

        # Assert
        self.assertEqual(result["name"], "AcmeEnclosure")
