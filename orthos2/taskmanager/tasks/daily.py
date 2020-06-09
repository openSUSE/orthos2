import logging

from data.models import Machine
from taskmanager.models import Task, TaskManager

logger = logging.getLogger('tasks')


class DailyMachineChecks(Task):
    """
    Triggers full machine check/scan for all qualified machines.
    """

    def __init__(self):
        pass

    def execute(self):
        """
        Executes the task.
        """
        for machine in Machine.objects.all():

            # only status check for administrative machines
            if machine.administrative or machine.system.administrative:
                machine.scan('status')
            else:
                machine.scan('all')


class DailyCheckReservationExpirations(Task):
    """
    Checks for expiring reservations for reserved machines.
    """

    def __init__(self):
        pass

    def execute(self):
        """
        Executes the task.
        """
        from taskmanager import tasks

        for machine in Machine.objects.all():
            if machine.administrative or machine.system.administrative:
                continue

            if machine.reserved_by and not machine.is_reserved_infinite():
                task = tasks.CheckReservationExpiration(machine.fqdn)
                TaskManager.add(task)
