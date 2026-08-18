from django.test import TestCase

from orthos2.api.serializers.domainarchitecture import DomainArchitectureSerializer
from orthos2.data.models import Architecture, Domain, DomainAdmin, ServerConfig


class DomainArchitectureSerializerTest(TestCase):
    """
    Verify that domain architecture serialization is working as expected.
    """

    def setUp(self) -> None:
        ServerConfig.objects.create(key="domain.validendings", value="orthos2.test")
        self.domain = Domain.objects.create(
            name="orthos2.test",
            ip_v4="127.0.0.1",
            ip_v6="::1",
            dynamic_range_v4_start="127.0.0.1",
            dynamic_range_v4_end="127.0.0.1",
            dynamic_range_v6_start="::1",
            dynamic_range_v6_end="::1",
        )
        self.architecture = Architecture.objects.get(name="x86_64")

    def test_serialization(self) -> None:
        """
        Verify that domain architecture serialization is working as expected.
        """
        # Arrange
        domainarchitecture = DomainAdmin.objects.create(
            domain=self.domain,
            arch=self.architecture,
            contact_email="support@orthos2.test",
        )
        serializer = DomainArchitectureSerializer(domainarchitecture)

        # Act
        result = serializer.data_info

        # Assert
        self.assertEqual(result["domain"], self.domain.pk)
        self.assertEqual(result["arch"], self.architecture.pk)
        self.assertEqual(result["contact_email"], "support@orthos2.test")
