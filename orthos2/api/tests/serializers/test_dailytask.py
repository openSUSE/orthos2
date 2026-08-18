from django.test import TestCase

from orthos2.api.serializers.dailytask import DailyTaskSerializer
from orthos2.taskmanager.models import DailyTask


class DailyTaskSerializerTest(TestCase):
    """
    Verify that daily task serialization is working as expected.
    """

    def test_serialization(self) -> None:
        """
        Verify that daily task serialization is working as expected.
        """
        # Arrange
        dailytask = DailyTask.objects.create(
            name="AcmeDailyTask", module="acme.module", arguments="[[], {}]"
        )
        serializer = DailyTaskSerializer(dailytask)

        # Act
        result = serializer.data_info

        # Assert
        self.assertEqual(result["name"], "AcmeDailyTask")
