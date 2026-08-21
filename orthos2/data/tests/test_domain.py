from django.core.exceptions import ValidationError
from django.test import TestCase

from orthos2.data.models import Domain, ServerConfig


class DomainDeleteProtectionTest(TestCase):
    """Domains referenced by machines must not be deletable."""

    fixtures = ["orthos2/data/fixtures/tests/test_machines.json"]

    def test_delete_raises_when_machines_exist(self) -> None:
        # Domain pk=1 (example.our-org.tld) is referenced by fixture machines.
        domain = Domain.objects.get(pk=1)
        with self.assertRaises(ValidationError):
            domain.delete()
        assert Domain.objects.filter(pk=domain.pk).exists()

    def test_delete_succeeds_without_machines(self) -> None:
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
        domain.delete()
        assert not Domain.objects.filter(pk=domain.pk).exists()
