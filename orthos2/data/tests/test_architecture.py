from django.core.exceptions import ValidationError
from django.test import TestCase

from orthos2.data.models import Architecture


class ArchitectureDeleteProtectionTest(TestCase):
    """Architectures referenced by machines must not be deletable."""

    fixtures = ["orthos2/utils/tests/fixtures/machines.json"]

    def test_delete_raises_when_machines_exist(self) -> None:
        # Architecture pk=1 (x86_64) is referenced by fixture machines.
        architecture = Architecture.objects.get(pk=1)
        with self.assertRaises(ValidationError):
            architecture.delete()
        assert Architecture.objects.filter(pk=architecture.pk).exists()

    def test_delete_succeeds_without_machines(self) -> None:
        architecture = Architecture.objects.create(name="AcmeArchitecture")
        architecture.delete()
        assert not Architecture.objects.filter(pk=architecture.pk).exists()
