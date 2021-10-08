import logging

from orthos2.data.models import Machine
from orthos2.taskmanager import tasks
from orthos2.taskmanager.models import Task, TaskManager
from orthos2.taskmanager.tasks.ansible import Ansible

logger = logging.getLogger('tasks')


class DailyMachineChecks(Task):
    """Trigger full machine check/scan for all qualified machines."""

    is_running = False

    def __init__(self):
        if DailyMachineChecks.is_running:
            raise Exception("Scan via already running")
        DailyMachineChecks.is_running = True

    @staticmethod
    def do_scan_all():
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
        """
        for machine in Machine.objects.all():
            if machine.administrative or machine.system.administrative:
                continue
            ansible_scan.append(machine.fqdn)
        """
        task = Ansible(ansible_scan)
        TaskManager.add(task)
        DailyMachineChecks.is_running = False

    def execute(self):
        """Execute the task."""
        DailyMachineChecks.do_scan_all()

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

class DailyCheckForPrimaryNetwork(Task):
    """ Check for machines without primary network interfaces and complain via email."""

    def __init_(self):
        pass

    def execute(self):
        """Execute the task."""
        from orthos2.taskmanager import tasks

        for machine in Machine.objects.all():
            task = tasks.CheckForPrimaryNetwork(machine.fqdn)
            TaskManager.add(task)
