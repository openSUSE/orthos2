from django.test import TestCase

from orthos2.api.serializers.devicetype import DeviceTypeSerializer
from orthos2.data.models import DeviceType, Manufacturer


class DeviceTypeSerializerTest(TestCase):
    """
    Verify that device type serialization is working as expected.
    """

    def test_serialization(self) -> None:
        """
        Verify that device type serialization is working as expected.
        """
        # Arrange
        manufacturer = Manufacturer.objects.create(name="AcmeCorp")
        devicetype = DeviceType.objects.create(
            name="AcmeDeviceType", manufacturer=manufacturer
        )
        serializer = DeviceTypeSerializer(devicetype)

        # Act
        result = serializer.data_info

        # Assert
        self.assertEqual(result["name"], "AcmeDeviceType")
