"""
Custom Ansible dynamic inventory plugin for Orthos2.

Reads machines from Django database based on task context.
Eliminates filesystem I/O for inventory generation.
"""

import os

from ansible.errors import AnsibleError
from ansible.plugins.inventory import BaseInventoryPlugin

# Initialize Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "orthos2.settings")
import django

django.setup()

from orthos2.data.models import Machine
from orthos2.taskmanager.models import SingleTask


class InventoryModule(BaseInventoryPlugin):
    """
    Orthos2 dynamic inventory plugin.

    Reads machine list from Task model via environment variable.
    Generates inventory with hostvars for callback plugin integration.
    """

    NAME = "orthos2"

    def verify_file(self, path):
        """Verify this is a valid inventory source for this plugin."""
        # Accept any .yml file with 'plugin: orthos2'
        if super().verify_file(path):
            if path.endswith(("orthos_dynamic.yml", "orthos2.yml")):
                return True
        return False

    def parse(self, inventory, loader, path, cache=True):
        """
        Parse inventory and populate with machines from database.

        Reads ORTHOS_SCAN_TASK_HASH from environment to find the task,
        then queries machines and populates inventory with hostvars.
        """
        super().parse(inventory, loader, path, cache)

        # Get task hash from environment variable
        task_hash = os.getenv("ORTHOS_SCAN_TASK_HASH")
        if not task_hash:
            raise AnsibleError(
                "ORTHOS_SCAN_TASK_HASH environment variable not set. "
                "This plugin requires the task hash to query machines."
            )

        # Query task from database
        try:
            task = SingleTask.objects.get(hash=task_hash)
        except SingleTask.DoesNotExist:
            raise AnsibleError(f"Task with hash {task_hash} not found in database")

        # Deserialize arguments to get machine list
        import ast

        args, kwargs = ast.literal_eval(task.arguments)
        machines_fqdns = args[0] if args else []

        if not machines_fqdns:
            raise AnsibleError(f"No machines found in task {task_hash} arguments")

        # Query Machine objects from database
        machines = Machine.objects.filter(fqdn__in=machines_fqdns)

        if not machines.exists():
            raise AnsibleError(
                f"No machines found in database for FQDNs: {machines_fqdns}"
            )

        # Create 'all' group
        group = inventory.add_group("all")

        # Add each machine as a host with hostvars
        for machine in machines:
            host_name = machine.fqdn

            # Add host to inventory
            inventory.add_host(host_name, group=group)

            # Set critical hostvar for callback plugin
            inventory.set_variable(host_name, "orthos2_machine_pk", machine.pk)

            # Set SSH connection parameters (from current inventory.template)
            inventory.set_variable(host_name, "ansible_connection", "ssh")
            inventory.set_variable(host_name, "ansible_user", "root")
            inventory.set_variable(
                host_name,
                "ansible_ssh_extra_args",
                "-o ConnectionAttempts=1 -o ConnectTimeout=5 -o StrictHostKeyChecking=no",
            )

        # Log successful inventory generation
        self.display.vvv(
            f"Orthos2 plugin: Generated inventory for {machines.count()} machines "
            f"from task {task_hash}"
        )
