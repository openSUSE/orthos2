from django.test import TestCase

from orthos2.api.serializers.remotepowerdevice import RemotePowerDeviceSerializer
from orthos2.data.models import RemotePowerDevice


class RemotePowerDeviceSerializerTest(TestCase):
    """
    Verify that remote power device serialization is working as expected.
    """

    fixtures = ["orthos2/api/fixtures/serializers/remotepowerdevice.json"]

    def test_serialization(self):
        """
        Verify that remote power device serialization is working as expected.
        """
        # Arrange
        remotepowerdevice = RemotePowerDevice.objects.get(pk=1)
        serializer = RemotePowerDeviceSerializer(remotepowerdevice)

        # Act
        result = serializer.data_info

        # Assert
        self.assertNotEqual(result, {})
