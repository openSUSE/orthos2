from django.test import TestCase

from orthos2.api.serializers.architecture import ArchitectureSerializer
from orthos2.data.models import Architecture


class ArchitectureSerializerTest(TestCase):
    """
    Verify that architecture serialization is working as expected.
    """

    def test_serialization(self) -> None:
        """
        Verify that architecture serialization is working as expected.
        """
        # Arrange
        architecture = Architecture.objects.create(name="AcmeArchitecture")
        serializer = ArchitectureSerializer(architecture)

        # Act
        result = serializer.data_info

        # Assert
        self.assertEqual(result["name"], "AcmeArchitecture")
