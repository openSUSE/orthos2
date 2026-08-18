from django.test import TestCase

from orthos2.api.serializers.vendor import VendorSerializer
from orthos2.data.models import Vendor


class VendorSerializerTest(TestCase):
    """
    Verify that vendor serialization is working as expected.
    """

    def test_serialization(self) -> None:
        """
        Verify that vendor serialization is working as expected.
        """
        # Arrange
        vendor = Vendor.objects.create(name="AcmeCorp")
        serializer = VendorSerializer(vendor)

        # Act
        result = serializer.data_info

        # Assert
        self.assertEqual(result["name"], "AcmeCorp")
