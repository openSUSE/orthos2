from django.test import TestCase

from orthos2.api.serializers.platform import PlatformSerializer
from orthos2.data.models import Manufacturer, Platform


class PlatformSerializerTest(TestCase):
    """
    Verify that platform serialization is working as expected.
    """

    def test_serialization(self) -> None:
        """
        Verify that platform serialization is working as expected.
        """
        # Arrange
        manufacturer = Manufacturer.objects.create(name="AcmeCorp")
        platform = Platform.objects.create(
            name="AcmePlatform", manufacturer=manufacturer
        )
        serializer = PlatformSerializer(platform)

        # Act
        result = serializer.data_info

        # Assert
        self.assertEqual(result["name"], "AcmePlatform")
