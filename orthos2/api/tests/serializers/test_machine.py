from django.test import TestCase

from orthos2.api.serializers.machine import MachineSerializer
from orthos2.data.models import Machine


class MachineSerializerTest(TestCase):
    """
    Verify that machine serialization is working as expected.
    """

    fixtures = [
        "orthos2/data/fixtures/systems.json",
        "orthos2/data/fixtures/vendors.json",
        "orthos2/api/fixtures/serializers/machines.json",
    ]

    def test_machine_serialization_infinite_reservation(self):
        """
        Verify that serializing machines with an infinite reservation is working as expected.
        """
        # Arrange
        machine = Machine.objects.get(pk=1)
        serializer = MachineSerializer(machine)

        # Act
        result = serializer.data_info

        # Assert
        self.assertNotEqual(result, {})
