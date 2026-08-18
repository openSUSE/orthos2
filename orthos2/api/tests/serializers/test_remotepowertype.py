from django.test import TestCase

from orthos2.api.serializers.remotepowertype import RemotePowerTypeSerializer
from orthos2.data.models import RemotePowerType


class RemotePowerTypeSerializerTest(TestCase):
    """
    Verify that remote power type serialization is working as expected.
    """

    def test_serialization(self) -> None:
        """
        Verify that remote power type serialization is working as expected.
        """
        # Arrange
        remotepowertype = RemotePowerType.objects.create(
            name="AcmeRemotePowerType", device="bmc"
        )
        serializer = RemotePowerTypeSerializer(remotepowertype)

        # Act
        result = serializer.data_info

        # Assert
        self.assertEqual(result["name"], "AcmeRemotePowerType")
        self.assertEqual(result["device"], "bmc")

    def test_serialization_excludes_password(self) -> None:
        """
        Verify that the password field is not exposed via the API.
        """
        # Arrange
        remotepowertype = RemotePowerType.objects.create(
            name="AcmeRemotePowerType", password="secret"
        )
        serializer = RemotePowerTypeSerializer(remotepowertype)

        # Act
        result = serializer.data_info

        # Assert
        self.assertNotIn("password", result)
