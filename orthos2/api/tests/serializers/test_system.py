from django.test import TestCase

from orthos2.api.serializers.system import SystemSerializer
from orthos2.data.models import System


class SystemSerializerTest(TestCase):
    """
    Verify that system serialization is working as expected.
    """

    def test_serialization(self) -> None:
        """
        Verify that system serialization is working as expected.
        """
        # Arrange
        system = System.objects.create(name="AcmeSystem")
        serializer = SystemSerializer(system)

        # Act
        result = serializer.data_info

        # Assert
        self.assertEqual(result["name"], "AcmeSystem")
