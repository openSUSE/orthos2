"""
Ansible scan result models.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from django.db import models
from django.utils import timezone

from orthos2.utils.misc import normalize_ascii

if TYPE_CHECKING:
    from orthos2.types import OptionalMachineForeignKey

logger = logging.getLogger("tasks")


class AnsibleScanResult(models.Model):
    """
    Historical record of Ansible fact gathering runs.

    Each scan creates a new record linked directly via machine PK.
    """

    # Direct link to Machine via PK (null only if callback error)
    machine: "OptionalMachineForeignKey" = models.ForeignKey(
        "Machine",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="ansible_scan_results",
        help_text="Machine this scan belongs to",
    )

    # Timing
    run_date = models.DateTimeField(
        default=timezone.now, db_index=True, help_text="When this scan was executed"
    )

    # Raw Ansible output
    facts_raw = models.JSONField(help_text="Complete ansible_facts dictionary as JSON")

    # Metadata
    ansible_version = models.CharField(
        max_length=50, blank=True, help_text="Ansible version used for this scan"
    )

    class Meta:
        ordering = ["-run_date"]
        indexes = [
            models.Index(fields=["machine", "-run_date"]),
        ]

    def __str__(self):
        return f"AnsibleScan({self.machine}, {self.run_date})"

    def apply_to_machine(self):
        """
        Parse facts_raw and update the linked Machine's fields.
        """
        if not self.machine:
            raise ValueError("Cannot apply to machine: no machine linked")

        machine = self.machine
        facts = self.facts_raw

        # Update CPU fields
        machine.cpu_physical = facts.get("ansible_processor_count", 1)
        machine.cpu_cores = machine.cpu_physical * facts.get(
            "ansible_processor_cores", 1
        )
        machine.cpu_threads = machine.cpu_cores * facts.get(
            "ansible_processor_threads_per_core", 1
        )
        machine.cpu_speed = Decimal(
            facts.get("ansible_local", {}).get("cpuinfo", {}).get("cpuspeed", 0.0)
        )
        machine.cpu_flags = (
            facts.get("ansible_local", {}).get("cpuinfo", {}).get("flags", "")
        )
        machine.cpu_id = (
            facts.get("ansible_local", {}).get("cpuinfo", {}).get("cpuid", "")
        )

        # Update CPU model
        processors = facts.get("ansible_processor", [])
        if processors and isinstance(processors, list):
            # ansible_processor contains: counts, vendor names, and model strings
            # We need to skip numeric entries and vendor names to get the actual model
            vendor_names = {"GenuineIntel", "AuthenticAMD", "ARM", "AARCH64"}

            for proc in processors:
                if isinstance(proc, str) and not proc.isdigit():
                    # Skip vendor name entries
                    if proc in vendor_names:
                        continue

                    # This should be the actual CPU model string
                    machine.cpu_model = proc
                    break

        # Update RAM
        if "ansible_memtotal_mb" in facts:
            machine.ram_amount = facts["ansible_memtotal_mb"]

        # Update kernel options
        cmdline = facts.get("ansible_cmdline", {})
        if isinstance(cmdline, dict):
            machine.kernel_options_discovered = " ".join(
                f"{k}={v}" if v else k for k, v in cmdline.items()
            )

        # Update disk information
        devices = facts.get("ansible_devices", {})
        if devices:
            # Find primary disk (usually sda or nvme0n1)
            for disk_name in ["sda", "nvme0n1", "vda"]:
                if disk_name in devices:
                    disk = devices[disk_name]
                    size_gb = disk.get("size", "").replace("GB", "").strip()
                    try:
                        machine.disk_primary_size = int(float(size_gb))
                    except (ValueError, TypeError):
                        pass

                    # Determine disk type (SSD vs HDD)
                    rotational = disk.get("rotational", "1")
                    machine.disk_type = "HDD" if rotational == "1" else "SSD"
                    break

        # Update BIOS information
        machine.bios_version = facts.get("ansible_bios_version", "")
        try:
            bios_date = facts.get("ansible_bios_date", "")
            if bios_date == "NA":
                bios_date = None
            if bios_date:
                # Django date fields must be in "%Y-%m-%d" format
                machine.bios_date = datetime.strptime(
                    bios_date, "%m/%d/%Y"  # type: ignore
                ).strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            logger.exception("Could not parse bios date [%s]", machine.fqdn)

        machine.efi = facts.get("ansible_local", {}).get("efi", {}).get("efi", False)

        # Update virtualization capability
        virt_role = facts.get("ansible_virtualization_role", "")
        machine.vm_capable = virt_role == "host"

        # Update hardware info fields (large text dumps)
        machine.lspci = normalize_ascii(
            "".join(
                facts.get("ansible_local", {})
                .get("lspci", {})
                .get("-vvv -nn", {})
                .get("stdout", "")
            )
        )
        machine.lsmod = normalize_ascii(
            "".join(
                facts.get("ansible_local", {})
                .get("lsmod", {})
                .get("noargs", {})
                .get("stdout", "")
            )
        )
        machine.lsusb = normalize_ascii(
            "".join(
                facts.get("ansible_local", {})
                .get("lsusb", {})
                .get("noargs", {})
                .get("stdout", "")
            )
        )
        machine.lsscsi = normalize_ascii(
            "".join(
                facts.get("ansible_local", {})
                .get("lsscsi", {})
                .get("-s", {})
                .get("stdout", "")
            )
        )
        machine.dmesg = (
            facts.get("ansible_local", {})
            .get("dmesg", {})
            .get("-xl", {})
            .get("stdout", "")
        )
        machine.dmidecode = (
            facts.get("ansible_local", {})
            .get("dmidecode", {})
            .get("noargs", {})
            .get("stdout", "")
        )
        machine.hwinfo = (
            facts.get("ansible_local", {})
            .get("hwinfo", {})
            .get("full", {})
            .get("stdout", "")
        )
        machine.last = facts.get("ansible_local", {}).get("last", {}).get("latest")
        machine.ipmi = facts.get("ansible_local", {}).get("ipmi", {}).get("ipmi", False)

        machine.save()
