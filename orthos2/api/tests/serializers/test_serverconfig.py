from django.test import TestCase

from orthos2.api.serializers.serverconfig import ServerConfigSerializer
from orthos2.data.models import ServerConfig


class ServerConfigSerializerTest(TestCase):
    """
    Verify that server configuration serialization is working as expected.
    """

    def test_serialization(self) -> None:
        """
        Verify that server configuration serialization is working as expected.
        """
        # Arrange
        serverconfig = ServerConfig.objects.create(
            key="acme.test.key", value="acme-value"
        )
        serializer = ServerConfigSerializer(serverconfig)

        # Act
        result = serializer.data_info

        # Assert
        self.assertEqual(result["key"], "acme.test.key")
        self.assertEqual(result["value"], "acme-value")
