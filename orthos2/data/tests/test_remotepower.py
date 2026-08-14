from django.test import TestCase

from orthos2.data.models import (
    Domain,
    Machine,
    RemotePower,
    RemotePowerDevice,
    RemotePowerType,
)


class RemotePowerSaveTests(TestCase):
    """
    RemotePower.save() dispatches on the fence agent's "device" value to
    decide which fields to populate/validate. This must actually match the
    real choices of RemotePowerType.device ("bmc", "rpowerdevice",
    "hypervisor") - a stale/misspelled literal here means an entire class of
    RemotePower never saves successfully.
    """

    fixtures = [
        "orthos2/data/fixtures/systems.json",
        "orthos2/data/fixtures/tests/test_machines.json",
    ]

    def setUp(self) -> None:
        domain = Domain.objects.get(name="example.our-org.tld")
        self.fence_agent = RemotePowerType.objects.create(
            name="test-pdu", device="rpowerdevice"
        )
        self.remote_power_device = RemotePowerDevice.objects.create(
            fqdn="pdu.example.our-org.tld",
            mac="AA:BB:CC:DD:EE:F0",
            fence_agent=self.fence_agent,
            domain=domain,
            architecture_id=1,
        )
        self.machine = Machine.objects.get(fqdn="test.testing.suse.de")

    def test_save_with_remote_power_device_backed_fence_agent(self) -> None:
        """
        Regression test: RemotePower.save() used to compare the fence agent's
        device against "rpower_device" (an underscore-containing value that
        no longer matches RemotePowerType.device's actual "rpowerdevice"
        choice), so this branch was silently unreachable and fell through to
        a final "else" that itself crashed with a TypeError.
        """
        remote_power = RemotePower(
            machine=self.machine, remote_power_device=self.remote_power_device
        )

        remote_power.save()

        remote_power.refresh_from_db()
        self.assertEqual(remote_power.fence_agent, self.fence_agent)
