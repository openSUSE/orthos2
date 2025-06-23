"""
This module contains all tasks that need to be performed together with NetBox.
"""

import logging

from django.core.exceptions import ObjectDoesNotExist

from orthos2.data.models.enclosure import Enclosure
from orthos2.data.models.machine import Machine
from orthos2.taskmanager.models import Task

logger = logging.getLogger("tasks")


class NetboxFetchEnclosure(Task):
    """
    Fetch information from Netbox API for an enclosure.
    """

    def execute(self) -> None:
        """
        Executes the task.
        """
        logger.info("Fetching information from Netbox API for all enclosures.")
        for enclosure in Enclosure.objects.all():
            logger.debug('Fetching enclosure "%s" - Start', enclosure.name)
            enclosure.fetch_netbox()
            logger.debug('Fetching enclosure "%s" - End', enclosure.name)


class NetboxFetchFullMachine(Task):
    """
    Fetch a single full machine with its subobjects.
    """

    def __init__(self, machine_id: int) -> None:
        """
        Constructor to initialize the task.
        """
        self.machine_pk = machine_id

    def execute(self) -> None:
        """
        Executes the task.
        """
        logger.info("Fetching information from Netbox API for all machines.")
        try:
            machine = Machine.objects.get(pk=self.machine_pk)
        except ObjectDoesNotExist as err:
            raise ValueError("Requested machine doesn't exist!") from err
        machine.enclosure.fetch_netbox()
