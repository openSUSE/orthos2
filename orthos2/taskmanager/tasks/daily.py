import logging

from orthos2.data.models import Machine
from orthos2.taskmanager import tasks
from orthos2.taskmanager.models import Task, TaskManager
from orthos2.taskmanager.tasks.ansible import Ansible

logger = logging.getLogger('tasks')


class DailyMachineChecks(Task):
    """Trigger full machine check/scan for all qualified machines."""

    def __init__(self):
        pass

    def execute(self):
        """Execute the task."""
        ansible_scan = []
        for machine in Machine.objects.all():
            # only status check for administrative machines
            if machine.administrative or machine.system.administrative:
                action = 'status'
            else:
                action = 'all'
                ansible_scan.append(machine.fqdn)
            task = tasks.MachineCheck(machine.fqdn,
                                      tasks.MachineCheck.Scan.to_int(action))
            TaskManager.add(task)

        #ToDo: Better wait until individual machine scans finished
        task = Ansible(ansible_scan)
        TaskManager.add(task)

class DailyCheckReservationExpirations(Task):
    """Check for expiring reservations for reserved machines."""

    def __init__(self):
        pass

    def execute(self):
        """Execute the task."""
        from orthos2.taskmanager import tasks

        for machine in Machine.objects.all():
            if machine.administrative or machine.system.administrative:
                continue

            if machine.reserved_by and not machine.is_reserved_infinite():
                task = tasks.CheckReservationExpiration(machine.fqdn)
                TaskManager.add(task)
