"""
Ansible task for scanning machines and storing results in database.

Results are stored via callback plugin in AnsibleScanResult model.
Inventory is generated in-memory by dynamic inventory plugin.
Zero filesystem dependencies for scan results and inventory.
"""

import logging
import os
from typing import List

from django.utils import timezone

from orthos2.data.models import AnsibleScanResult
from orthos2.taskmanager.models import Task
from orthos2.utils.misc import execute


class Ansible(Task):

    facts_dir = "/usr/lib/orthos2/ansible"

    def __init__(self, machines: List[str]) -> None:
        """
        Initialize Ansible scan task.

        param machines: List of machine FQDNs to scan via Ansible
        """
        self.logger = logging.getLogger("tasks")
        self.machines = machines

    def execute(self) -> None:
        """
        Execute Ansible scan using dynamic inventory plugin.

        The plugin reads machines from database via task hash.
        Results are stored directly to database via callback plugin.
        Zero filesystem I/O for inventory and scan results.
        """
        # Generate task hash to pass to plugin via environment variable
        import json
        from hashlib import sha1

        # Generate hash same way as BaseTask.generate_hash()
        hash_input = (
            f"{self.__class__.__name__}"
            f"{self.__class__.__module__}"
            f"{json.dumps(self._Task__arguments)}"  # type: ignore
        ).encode("utf-8")
        task_hash = sha1(hash_input).hexdigest()

        # Set environment variable for dynamic inventory plugin
        os.environ["ORTHOS_SCAN_TASK_HASH"] = task_hash

        try:
            # Record scan start time to identify results from this run
            scan_start = timezone.now()

            # Execute ansible-playbook with dynamic inventory
            command = (
                f"/usr/bin/ansible-playbook "
                f"-i {Ansible.facts_dir}/orthos_dynamic.yml "
                f"{Ansible.facts_dir}/site.yml"
            )
            stdout, stderr, returncode = execute(command, cwd=Ansible.facts_dir)
            self.logger.debug("Calling: %s - %d", command, returncode)
            self.logger.debug("ansible: %s - %s - %s", stdout, stderr, returncode)

            if returncode != 0:
                self.logger.error(
                    "Ansible playbook failed with return code %d", returncode
                )
                self.logger.error("stderr: %s", stderr)
                raise RuntimeError(f"Ansible playbook failed: {stderr}")

            # Check database for scan results from this run
            recent_results = AnsibleScanResult.objects.filter(run_date__gte=scan_start)

            scanned_machines = set(
                recent_results.values_list("machine__fqdn", flat=True).distinct()
            )
            expected_machines = set(self.machines)
            missing_machines = expected_machines - scanned_machines

            if missing_machines:
                self.logger.warning(
                    "No scan results found in database for machines: %s",
                    ", ".join(missing_machines),
                )

            self.logger.info(
                "Successfully scanned %d/%d machines via ansible",
                len(scanned_machines),
                len(expected_machines),
            )
        finally:
            # Clean up environment variable
            if "ORTHOS_SCAN_TASK_HASH" in os.environ:
                del os.environ["ORTHOS_SCAN_TASK_HASH"]
