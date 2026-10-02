"""Tests for MachineCheck.status() sourcing IPv4/IPv6/SSH from Prometheus."""

from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase

from orthos2.data.models import ServerConfig
from orthos2.data.models.machine import Machine
from orthos2.taskmanager.tasks.machinetasks import MachineCheck


class MachineCheckStatusTest(TestCase):
    """`Machine.objects.get(pk=2)` (fqdn `testsys.orthos2.test`) has a BMC
    (`testsys-sp.orthos2.test`) and `check_connectivity=ALL` in the shared fixture."""

    fixtures = [
        "orthos2/utils/tests/fixtures/machines.json",
    ]

    def setUp(self) -> None:
        cache.clear()
        ServerConfig.objects.update_or_create(
            key="domain.validendings", defaults={"value": "orthos2.test"}
        )
        self.machine = Machine.objects.get(pk=2)
        # The fixture's "BareMetal" System doesn't allow BMCs by default, which would make
        # the re-save() at the end of status() reject this already-BMC-attached machine.
        self.machine.system.allowBMC = True
        self.machine.system.save()
        self.task = MachineCheck(fqdn=self.machine.fqdn, scan=MachineCheck.Scan.STATUS)
        self.task.machine = self.machine

    def tearDown(self) -> None:
        cache.clear()

    def test_status_sets_ipv4_and_ipv6_reachable_from_prometheus(self) -> None:
        with patch(
            "orthos2.taskmanager.tasks.machinetasks.Prometheus.get_instance"
        ) as get_instance:
            get_instance.return_value.probe_success_map.side_effect = lambda job: {
                "icmp-arch-ipv4": {self.machine.fqdn: True},
                "icmp-arch-ipv6": {self.machine.fqdn: False},
            }.get(job, {})
            with patch(
                "orthos2.taskmanager.tasks.machinetasks.login_test",
                return_value=True,
            ):
                self.task.status()

        self.machine.refresh_from_db()
        self.assertEqual(self.machine.status_ipv4, Machine.StatusIP.REACHABLE)
        self.assertEqual(self.machine.status_ipv6, Machine.StatusIP.UNREACHABLE)

    def test_status_sets_ssh_from_prometheus_and_still_runs_local_login_test(
        self,
    ) -> None:
        with patch(
            "orthos2.taskmanager.tasks.machinetasks.Prometheus.get_instance"
        ) as get_instance:
            get_instance.return_value.probe_success_map.side_effect = lambda job: {
                "icmp-arch-ipv4": {self.machine.fqdn: True},
                "icmp-arch-ipv6": {self.machine.fqdn: True},
                "ssh-arch": {self.machine.fqdn: True},
            }.get(job, {})
            with patch(
                "orthos2.taskmanager.tasks.machinetasks.login_test",
                return_value=True,
            ) as login_test_mock:
                self.task.status()

        self.machine.refresh_from_db()
        self.assertTrue(self.machine.status_ssh)
        self.assertTrue(self.machine.status_login)
        login_test_mock.assert_called_once_with(self.machine.fqdn)

    def test_status_does_not_attempt_login_when_ssh_unreachable(self) -> None:
        with patch(
            "orthos2.taskmanager.tasks.machinetasks.Prometheus.get_instance"
        ) as get_instance:
            get_instance.return_value.probe_success_map.side_effect = lambda job: {
                "icmp-arch-ipv4": {self.machine.fqdn: True},
                "icmp-arch-ipv6": {self.machine.fqdn: True},
                "ssh-arch": {self.machine.fqdn: False},
            }.get(job, {})
            with patch(
                "orthos2.taskmanager.tasks.machinetasks.login_test"
            ) as login_test_mock:
                self.task.status()

        self.machine.refresh_from_db()
        self.assertFalse(self.machine.status_ssh)
        self.assertFalse(self.machine.status_login)
        login_test_mock.assert_not_called()

    def test_status_sets_bmc_status_from_prometheus(self) -> None:
        bmc = self.machine.bmc
        with patch(
            "orthos2.taskmanager.tasks.machinetasks.Prometheus.get_instance"
        ) as get_instance:
            get_instance.return_value.probe_success_map.side_effect = lambda job: {
                "icmp-arch-ipv4": {
                    self.machine.fqdn: True,
                    bmc.fqdn: True,
                },
                "icmp-arch-ipv6": {},
                "ssh-arch": {},
            }.get(job, {})
            with patch(
                "orthos2.taskmanager.tasks.machinetasks.login_test",
                return_value=False,
            ):
                self.task.status()

        bmc.refresh_from_db()
        self.assertEqual(bmc.status_ipv4, Machine.StatusIP.REACHABLE)
        self.assertEqual(bmc.status_ipv6, Machine.StatusIP.UNREACHABLE)

    def test_status_respects_connectivity_none(self) -> None:
        self.machine.check_connectivity = Machine.Connectivity.NONE
        self.machine.save()

        with patch(
            "orthos2.taskmanager.tasks.machinetasks.Prometheus.get_instance"
        ) as get_instance:
            self.task.status()
            get_instance.return_value.probe_success_map.assert_not_called()

        self.machine.refresh_from_db()
        self.assertEqual(self.machine.status_ipv4, Machine.StatusIP.UNREACHABLE)
        self.assertFalse(self.machine.status_ssh)
        self.assertFalse(self.machine.status_login)

    def test_status_caches_probe_success_map_per_job(self) -> None:
        """A second `MachineCheck.status()` call within the cache TTL must not
        re-query Prometheus for the same job."""
        other_machine = Machine.objects.get(pk=1)
        other_task = MachineCheck(
            fqdn=other_machine.fqdn, scan=MachineCheck.Scan.STATUS
        )
        other_task.machine = other_machine

        with patch(
            "orthos2.taskmanager.tasks.machinetasks.Prometheus.get_instance"
        ) as get_instance:
            # Both machines reachable on ipv4, so the ssh-arch job also gets queried
            # (gated on `status_ping`) - exercising all 3 jobs' caching in one go.
            get_instance.return_value.probe_success_map.side_effect = lambda job: (
                {self.machine.fqdn: True, other_machine.fqdn: True}
                if job == "icmp-arch-ipv4"
                else {}
            )
            with patch("orthos2.taskmanager.tasks.machinetasks.login_test"):
                self.task.status()
                other_task.status()

            # 3 jobs (ipv4/ipv6/ssh) queried once each, not once per machine.
            self.assertEqual(get_instance.return_value.probe_success_map.call_count, 3)
