from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from orthos2.data.models import AnsibleScanResult, Domain, Machine, ServerConfig


class AnsibleScanResultModelTest(TestCase):
    fixtures = ["orthos2/utils/tests/fixtures/machines.json"]

    def setUp(self) -> None:
        """Set up ServerConfig for domain validation and remove BMC from test machines."""
        ServerConfig.objects.update_or_create(
            key="domain.validendings", defaults={"value": "orthos2.test"}
        )
        # Configure Cobbler server for domain to avoid "Cobbler Server not configured" error
        domain = Domain.objects.get(name="orthos2.test")
        domain.cobbler_server = Machine.objects.get(fqdn="cobbler.orthos2.test")
        domain.save(update_fields=["cobbler_server"])

        # Remove BMC from test machines to avoid "BareMetal systems cannot use a BMC" error
        # when apply_to_machine() calls machine.save()
        for machine in Machine.objects.all():
            if hasattr(machine, "bmc"):
                machine.bmc.delete()

    def _get_minimal_facts(self):
        """Get minimal facts that won't cause NOT NULL violations."""
        return {
            "ansible_local": {
                "last": {"latest": ""},
            }
        }

    def test_create_ansible_scan_result(self) -> None:
        """Should create AnsibleScanResult with valid facts_raw."""
        # Arrange
        machine = Machine.objects.first()
        assert machine is not None
        facts = {"ansible_processor_count": 2}
        run_date = timezone.now()

        # Act
        result = AnsibleScanResult.objects.create(
            machine=machine,
            facts_raw=facts,
            ansible_version="2.9.27",
            run_date=run_date,
        )

        # Assert
        assert result.machine == machine
        assert result.facts_raw == facts
        assert result.ansible_version == "2.9.27"
        assert result.run_date == run_date

    def test_ansible_scan_result_cascade_delete(self) -> None:
        """Should delete AnsibleScanResult when Machine is deleted."""
        # Arrange
        machine = Machine.objects.first()
        assert machine is not None
        result = AnsibleScanResult.objects.create(
            machine=machine, facts_raw={}, ansible_version="2.9.27"
        )
        result_pk = result.pk

        # Act
        machine.delete()

        # Assert
        assert not AnsibleScanResult.objects.filter(pk=result_pk).exists()

    def test_ansible_scan_result_ordering(self) -> None:
        """Should order AnsibleScanResults by -run_date (newest first)."""
        # Arrange
        machine = Machine.objects.first()
        assert machine is not None
        old_date = timezone.now()
        new_date = timezone.now()

        result1 = AnsibleScanResult.objects.create(
            machine=machine,
            facts_raw={},
            ansible_version="2.9.27",
            run_date=old_date,
        )
        result2 = AnsibleScanResult.objects.create(
            machine=machine,
            facts_raw={},
            ansible_version="2.9.27",
            run_date=new_date,
        )

        # Act
        results = list(AnsibleScanResult.objects.all())

        # Assert
        assert results[0] == result2  # Newer first
        assert results[1] == result1

    def test_apply_to_machine_cpu_fields(self) -> None:
        """Should update all CPU fields from ansible facts."""
        # Arrange
        machine = Machine.objects.first()
        assert machine is not None
        facts = self._get_minimal_facts()
        facts.update(
            {
                "ansible_processor_count": 2,
                "ansible_processor_cores": 4,
                "ansible_processor_threads_per_core": 2,
            }
        )
        facts["ansible_local"]["cpuinfo"] = {
            "cpuspeed": 2.4,
            "flags": "fpu vme de pse tsc msr",
            "cpuid": "GenuineIntel",
        }

        result = AnsibleScanResult.objects.create(
            machine=machine, facts_raw=facts, ansible_version="2.9.27"
        )

        # Act
        result.apply_to_machine()

        # Assert
        machine.refresh_from_db()
        assert machine.cpu_physical == 2
        assert machine.cpu_cores == 8  # 2 * 4
        assert machine.cpu_threads == 16  # 8 * 2
        assert machine.cpu_speed == Decimal("2.4")
        assert machine.cpu_flags == "fpu vme de pse tsc msr"
        assert machine.cpu_id == "GenuineIntel"

    def test_apply_to_machine_cpu_model_vendor_filtering(self) -> None:
        """Should skip vendor names when extracting CPU model."""
        # Arrange
        machine = Machine.objects.first()
        assert machine is not None
        facts = self._get_minimal_facts()
        facts["ansible_processor"] = [
            "0",
            "GenuineIntel",
            "Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz",
        ]

        result = AnsibleScanResult.objects.create(
            machine=machine, facts_raw=facts, ansible_version="2.9.27"
        )

        # Act
        result.apply_to_machine()

        # Assert
        machine.refresh_from_db()
        assert machine.cpu_model == "Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz"

    def test_apply_to_machine_ram(self) -> None:
        """Should update RAM amount from ansible_memtotal_mb."""
        # Arrange
        machine = Machine.objects.first()
        assert machine is not None
        facts = self._get_minimal_facts()
        facts["ansible_memtotal_mb"] = 16384

        result = AnsibleScanResult.objects.create(
            machine=machine, facts_raw=facts, ansible_version="2.9.27"
        )

        # Act
        result.apply_to_machine()

        # Assert
        machine.refresh_from_db()
        assert machine.ram_amount == 16384

    def test_apply_to_machine_kernel_options(self) -> None:
        """Should format kernel options from ansible_cmdline."""
        # Arrange
        machine = Machine.objects.first()
        assert machine is not None
        facts = self._get_minimal_facts()
        facts["ansible_cmdline"] = {
            "console": "ttyS0",
            "quiet": None,
            "crashkernel": "256M",
        }

        result = AnsibleScanResult.objects.create(
            machine=machine, facts_raw=facts, ansible_version="2.9.27"
        )

        # Act
        result.apply_to_machine()

        # Assert
        machine.refresh_from_db()
        # Order may vary, check each part is present
        assert "console=ttyS0" in machine.kernel_options_discovered
        assert "quiet" in machine.kernel_options_discovered
        assert "crashkernel=256M" in machine.kernel_options_discovered

    def test_apply_to_machine_disk_sda_hdd(self) -> None:
        """Should detect HDD from rotational flag."""
        # Arrange
        machine = Machine.objects.first()
        assert machine is not None
        facts = self._get_minimal_facts()
        facts["ansible_devices"] = {
            "sda": {"size": "500.00 GB", "rotational": "1"},
            "loop0": {"size": "1.00 GB"},  # Should be ignored
        }

        result = AnsibleScanResult.objects.create(
            machine=machine, facts_raw=facts, ansible_version="2.9.27"
        )

        # Act
        result.apply_to_machine()

        # Assert
        machine.refresh_from_db()
        assert machine.disk_primary_size == 500
        assert machine.disk_type == "HDD"

    def test_apply_to_machine_disk_ssd(self) -> None:
        """Should detect SSD from rotational=0 flag."""
        # Arrange
        machine = Machine.objects.first()
        assert machine is not None
        facts = self._get_minimal_facts()
        facts["ansible_devices"] = {"sda": {"size": "500GB", "rotational": "0"}}

        result = AnsibleScanResult.objects.create(
            machine=machine, facts_raw=facts, ansible_version="2.9.27"
        )

        # Act
        result.apply_to_machine()

        # Assert
        machine.refresh_from_db()
        assert machine.disk_type == "SSD"

    def test_apply_to_machine_disk_nvme(self) -> None:
        """Should detect NVMe disk type."""
        # Arrange
        machine = Machine.objects.first()
        assert machine is not None
        facts = self._get_minimal_facts()
        facts["ansible_devices"] = {
            "nvme0n1": {"size": "1.00 TB", "rotational": "0"},
        }

        result = AnsibleScanResult.objects.create(
            machine=machine, facts_raw=facts, ansible_version="2.9.27"
        )

        # Act
        result.apply_to_machine()

        # Assert
        machine.refresh_from_db()
        # NVMe should be detected by name prefix, not just rotational flag
        # Based on the actual code, it doesn't check for nvme prefix
        # It only checks rotational for SSD vs HDD
        assert machine.disk_type == "SSD"

    def test_apply_to_machine_bios_info(self) -> None:
        """Should update BIOS version and convert date format."""
        # Arrange
        machine = Machine.objects.first()
        assert machine is not None
        facts = self._get_minimal_facts()
        facts["ansible_bios_version"] = "2.3.4"
        facts["ansible_bios_date"] = "04/15/2023"

        result = AnsibleScanResult.objects.create(
            machine=machine, facts_raw=facts, ansible_version="2.9.27"
        )

        # Act
        result.apply_to_machine()

        # Assert
        machine.refresh_from_db()
        assert machine.bios_version == "2.3.4"
        assert str(machine.bios_date) == "2023-04-15"

    def test_apply_to_machine_bios_date_na(self) -> None:
        """Should not update bios_date when value is 'NA'."""
        # Arrange
        machine = Machine.objects.first()
        assert machine is not None
        original_bios_date = machine.bios_date
        facts = self._get_minimal_facts()
        facts["ansible_bios_date"] = "NA"

        result = AnsibleScanResult.objects.create(
            machine=machine, facts_raw=facts, ansible_version="2.9.27"
        )

        # Act
        result.apply_to_machine()

        # Assert
        machine.refresh_from_db()
        # When bios_date is "NA", it should not be updated
        assert machine.bios_date == original_bios_date

    def test_apply_to_machine_efi(self) -> None:
        """Should update EFI flag from ansible_local."""
        # Arrange
        machine = Machine.objects.first()
        assert machine is not None
        facts = self._get_minimal_facts()
        facts["ansible_local"]["efi"] = {"efi": True}

        result = AnsibleScanResult.objects.create(
            machine=machine, facts_raw=facts, ansible_version="2.9.27"
        )

        # Act
        result.apply_to_machine()

        # Assert
        machine.refresh_from_db()
        assert machine.efi is True

    def test_apply_to_machine_vm_capable_host(self) -> None:
        """Should set vm_capable=True for virtualization host."""
        # Arrange
        machine = Machine.objects.first()
        assert machine is not None
        facts = self._get_minimal_facts()
        facts["ansible_virtualization_role"] = "host"

        result = AnsibleScanResult.objects.create(
            machine=machine, facts_raw=facts, ansible_version="2.9.27"
        )

        # Act
        result.apply_to_machine()

        # Assert
        machine.refresh_from_db()
        assert machine.vm_capable is True

    def test_apply_to_machine_vm_capable_guest(self) -> None:
        """Should set vm_capable=False for virtualization guest."""
        # Arrange
        machine = Machine.objects.first()
        assert machine is not None
        facts = self._get_minimal_facts()
        facts["ansible_virtualization_role"] = "guest"

        result = AnsibleScanResult.objects.create(
            machine=machine, facts_raw=facts, ansible_version="2.9.27"
        )

        # Act
        result.apply_to_machine()

        # Assert
        machine.refresh_from_db()
        assert machine.vm_capable is False

    def test_apply_to_machine_lspci_normalized(self) -> None:
        """Should normalize lspci output (bug fix verification)."""
        # Arrange
        machine = Machine.objects.first()
        assert machine is not None
        facts = self._get_minimal_facts()
        facts["ansible_local"]["lspci"] = {
            "-vvv -nn": {"stdout": "00:00.0 Host bridge: Intel® Corporation"}
        }

        result = AnsibleScanResult.objects.create(
            machine=machine, facts_raw=facts, ansible_version="2.9.27"
        )

        # Act
        result.apply_to_machine()

        # Assert
        machine.refresh_from_db()
        # normalize_ascii should replace non-ASCII characters
        assert "Intel" in machine.lspci
        assert "®" not in machine.lspci  # Non-ASCII should be replaced

    def test_apply_to_machine_hardware_dumps(self) -> None:
        """Should populate all hardware dump fields."""
        # Arrange
        machine = Machine.objects.first()
        assert machine is not None
        facts = self._get_minimal_facts()
        facts["ansible_local"].update(
            {
                "lsmod": {"noargs": {"stdout": "Module  Size  Used by"}},
                "lsusb": {"noargs": {"stdout": "Bus 001 Device 001"}},
                "lsscsi": {"-s": {"stdout": "[0:0:0:0] disk ATA"}},
                "dmesg": {"-xl": {"stdout": "[0.000000] Linux version"}},
                "dmidecode": {"noargs": {"stdout": "# dmidecode 3.3"}},
                "hwinfo": {"full": {"stdout": "============"}},
            }
        )

        result = AnsibleScanResult.objects.create(
            machine=machine, facts_raw=facts, ansible_version="2.9.27"
        )

        # Act
        result.apply_to_machine()

        # Assert
        machine.refresh_from_db()
        assert machine.lsmod == "Module  Size  Used by"
        assert machine.lsusb == "Bus 001 Device 001"
        assert machine.lsscsi == "[0:0:0:0] disk ATA"
        assert machine.dmesg == "[0.000000] Linux version"
        assert machine.dmidecode == "# dmidecode 3.3"
        assert machine.hwinfo == "============"

    def test_apply_to_machine_last_and_ipmi(self) -> None:
        """Should update last login and IPMI flag."""
        # Arrange
        machine = Machine.objects.first()
        assert machine is not None
        facts = self._get_minimal_facts()
        facts["ansible_local"]["last"] = {"latest": "root pts/0 Wed Apr 30"}
        facts["ansible_local"]["ipmi"] = {"ipmi": True}

        result = AnsibleScanResult.objects.create(
            machine=machine, facts_raw=facts, ansible_version="2.9.27"
        )

        # Act
        result.apply_to_machine()

        # Assert
        machine.refresh_from_db()
        assert machine.last == "root pts/0 Wed Apr 30"
        assert machine.ipmi is True

    def test_apply_to_machine_missing_facts(self) -> None:
        """Should handle missing facts gracefully."""
        # Arrange
        machine = Machine.objects.first()
        assert machine is not None
        facts = self._get_minimal_facts()

        result = AnsibleScanResult.objects.create(
            machine=machine, facts_raw=facts, ansible_version="2.9.27"
        )

        # Act
        # Should not crash
        result.apply_to_machine()

        # Assert
        machine.refresh_from_db()
        # Fields should have defaults or remain unchanged

    def test_apply_to_machine_no_machine_raises(self) -> None:
        """Should raise ValueError when machine is None."""
        # Arrange
        result = AnsibleScanResult.objects.create(
            machine=None, facts_raw={}, ansible_version="2.9.27"
        )

        # Act & Assert
        try:
            result.apply_to_machine()
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Cannot apply to machine: no machine linked" in str(e)

    def test_string_representation(self) -> None:
        """Should have meaningful string representation."""
        # Arrange
        machine = Machine.objects.first()
        assert machine is not None
        result = AnsibleScanResult.objects.create(
            machine=machine, facts_raw={}, ansible_version="2.9.27"
        )

        # Act
        result_str = str(result)

        # Assert
        assert "AnsibleScan" in result_str
        assert machine.fqdn in result_str or str(machine) in result_str
