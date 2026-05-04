"""
Ansible callback plugin for storing scan results in Orthos2 database.
"""

import os

from ansible.executor.task_result import CallbackTaskResult
from ansible.plugins.callback import CallbackBase
from ansible.release import __version__ as ansible_version

# Initialize Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "orthos2.settings")

# Add project root to path if running from ansible
import django

django.setup()

from orthos2.data.models import AnsibleScanResult, Machine


class CallbackModule(CallbackBase):
    """
    Streams Ansible results to AnsibleScanResult model.
    """

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = "notification"
    CALLBACK_NAME = "orthos2_history"
    CALLBACK_NEEDS_ENABLED = True

    def v2_runner_on_ok(self, result: CallbackTaskResult):
        """Capture successful task results"""
        host = result._host.get_name()
        task_name = result._task.get_name()

        # Only process if ansible_facts were gathered
        if "ansible_facts" in result._result:
            facts = result._result["ansible_facts"]

            # Only save on the final comprehensive fact gathering task
            # This ensures we have all facts including custom facts from ansible_local
            if task_name != "Ensure all facts are gathered":
                self._display.v(
                    f"Skipping intermediate fact gathering task '{task_name}' for {host}"
                )
                return

            # Get injected machine PK from inventory
            hostvars = result._host.get_vars()
            machine_pk = hostvars.get("orthos2_machine_pk")

            if not machine_pk:
                self._display.warning(
                    f"No orthos2_machine_pk for {host}, skipping database storage"
                )
                return

            try:
                # Get machine instance
                try:
                    machine = Machine.objects.get(pk=machine_pk)
                except Machine.DoesNotExist:
                    self._display.error(
                        f"Machine with PK {machine_pk} not found for {host}"
                    )
                    return

                # Create AnsibleScanResult record
                scan_result = AnsibleScanResult(
                    machine=machine,
                    facts_raw=facts,
                    ansible_version=ansible_version,
                )

                # Save the record
                scan_result.save()

                # Optionally apply to machine immediately
                if os.getenv("ORTHOS_ANSIBLE_AUTO_APPLY", "true").lower() == "true":
                    scan_result.apply_to_machine()
                    self._display.display(
                        f"Stored and applied scan result for {host} (machine_pk={machine_pk})",
                        color="green",
                    )
                else:
                    self._display.display(
                        f"Stored scan result for {host} (machine_pk={machine_pk})",
                        color="green",
                    )

            except Exception as e:
                self._display.error(f"Failed to store scan result for {host}: {e}")
                # Don't let callback failures stop Ansible
                import traceback

                self._display.display(traceback.format_exc(), color="red")
