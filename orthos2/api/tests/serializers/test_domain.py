from django.test import TestCase

from orthos2.api.serializers.domain import DomainSerializer
from orthos2.data.models import Domain, ServerConfig


class DomainSerializerTest(TestCase):
    """
    Verify that domain serialization is working as expected.
    """

    def test_serialization(self) -> None:
        """
        Verify that domain serialization is working as expected.
        """
        # Arrange
        ServerConfig.objects.create(key="domain.validendings", value="orthos2.test")
        domain = Domain.objects.create(
            name="orthos2.test",
            ip_v4="127.0.0.1",
            ip_v6="::1",
            dynamic_range_v4_start="127.0.0.1",
            dynamic_range_v4_end="127.0.0.1",
            dynamic_range_v6_start="::1",
            dynamic_range_v6_end="::1",
        )
        serializer = DomainSerializer(domain)

        # Act
        result = serializer.data_info

        # Assert
        self.assertEqual(result["name"], "orthos2.test")

    def test_serialization_excludes_cobbler_server_password(self) -> None:
        """
        Verify that the cobbler server password field is not exposed via the API.
        """
        # Arrange
        ServerConfig.objects.create(key="domain.validendings", value="orthos2.test")
        domain = Domain.objects.create(
            name="orthos2.test",
            ip_v4="127.0.0.1",
            ip_v6="::1",
            dynamic_range_v4_start="127.0.0.1",
            dynamic_range_v4_end="127.0.0.1",
            dynamic_range_v6_start="::1",
            dynamic_range_v6_end="::1",
        )
        serializer = DomainSerializer(domain)

        # Act
        result = serializer.data_info

        # Assert
        self.assertNotIn("cobbler_server_password", result)
