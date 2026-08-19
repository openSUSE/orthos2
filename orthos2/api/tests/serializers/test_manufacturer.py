from django.test import TestCase

from orthos2.api.serializers.manufacturer import ManufacturerSerializer
from orthos2.data.models import Manufacturer


class ManufacturerSerializerTest(TestCase):
    """
    Verify that manufacturer serialization is working as expected.
    """

    def test_serialization(self) -> None:
        """
        Verify that manufacturer serialization is working as expected.
        """
        # Arrange
        manufacturer = Manufacturer.objects.create(name="AcmeCorp")
        serializer = ManufacturerSerializer(manufacturer)

        # Act
        result = serializer.data_info

        # Assert
        self.assertEqual(result["name"], "AcmeCorp")
