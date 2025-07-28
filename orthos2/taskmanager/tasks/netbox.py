"""
This module contains all tasks that need to be performed together with NetBox.
"""

import datetime
import logging

from django.core.exceptions import ObjectDoesNotExist

from orthos2.data.models import BMC, Enclosure, Machine, NetworkInterface
from orthos2.data.models.netboxorthoscomparision import NetboxOrthosComparisionRun
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


class NetboxFetchMachine(Task):
    """
    Iterate over all machines and fetch information from Netbox.
    """

    def execute(self) -> None:
        """
        Executes the task.
        """
        logger.info("Fetching information from Netbox API for all machines.")
        for machine in Machine.objects.all():
            logger.debug('Fetching machine "%s" - Start', machine.fqdn)
            machine.fetch_netbox()
            logger.debug('Fetching machine "%s" - End', machine.fqdn)


class NetboxFetchBMC(Task):
    """
    Iterate over all BMCs and try to match them to NetBox objects.
    """

    def execute(self) -> None:
        """
        Executes the task.
        """
        logger.info("Fetching information from Netbox API for all machines.")
        for bmc in BMC.objects.all():
            logger.debug('Fetching bmc "%s" - Start', bmc.mac)
            bmc.fetch_netbox()
            logger.debug('Fetching bmc "%s" - End', bmc.mac)


class NetboxFetchNetworkInterface(Task):
    """
    Iterate over all network interfaces and try to match them to NetBox objects.
    """

    def execute(self) -> None:
        """
        Executes the task.
        """
        logger.info("Fetching information from Netbox API for all machines.")
        for network_interface in NetworkInterface.objects.all():
            logger.debug(
                'Fetching network interface "%s" - Start', network_interface.name
            )
            network_interface.fetch_netbox()
            logger.debug(
                'Fetching network interface "%s" - End', network_interface.name
            )


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
        logger.info(
            "Fetching information from Netbox API for machine with pk %s.",
            self.machine_pk,
        )
        try:
            machine = Machine.objects.get(pk=self.machine_pk)
        except ObjectDoesNotExist as err:
            raise ValueError("Requested machine doesn't exist!") from err
        machine.enclosure.fetch_netbox()
        machine.fetch_netbox()
        if machine.has_bmc():
            machine.bmc.fetch_netbox()
        for intf in machine.networkinterfaces.all():
            intf.fetch_netbox()


class NetboxFetchFullEnclosure(Task):
    """
    Fetch a single enclosure.
    """

    def __init__(self, enclosure_id: int) -> None:
        """
        Constructor to initialize the task.
        """
        self.enclosure_pk = enclosure_id

    def execute(self) -> None:
        """
        Executes the task.
        """
        logger.info(
            "Fetching information from Netbox API for enclosure with pk %s.",
            self.enclosure_pk,
        )
        try:
            enclosure = Enclosure.objects.get(pk=self.enclosure_pk)
        except ObjectDoesNotExist as err:
            raise ValueError("Requested machine doesn't exist!") from err
        enclosure.fetch_netbox()


class NetboxCompareFullMachine(Task):
    """
    Compare a single full machine with its subobjects.
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
        logger.info(
            'Comparing information from Netbox API for machine "%s".', self.machine_pk
        )
        try:
            machine = Machine.objects.get(pk=self.machine_pk)
        except ObjectDoesNotExist as err:
            raise ValueError("Requested machine doesn't exist!") from err
        machine.enclosure.compare_netbox()
        machine.compare_netbox()
        if machine.has_bmc():
            machine.bmc.compare_netbox()
        for intf in machine.networkinterfaces.all():
            intf.compare_netbox()


class NetboxCompareEnclosure(Task):
    """
    Compare a single enclosure with its subobjects.
    """

    def __init__(self, enclosure_id: int) -> None:
        """
        Constructor to initialize the task.
        """
        self.enclosure_pk = enclosure_id

    def execute(self) -> None:
        """
        Executes the task.
        """
        logger.info(
            'Comparing information from Netbox API for enclosure "%s".',
            self.enclosure_pk,
        )
        try:
            enclosure = Enclosure.objects.get(pk=self.enclosure_pk)
        except ObjectDoesNotExist as err:
            raise ValueError("Requested enclosure doesn't exist!") from err
        enclosure.compare_netbox()


class NetboxCleanupComparisionResults(Task):
    """
    Cleanup old NetBox comparison results.
    """

    def execute(self) -> None:
        """
        Executes the task.
        """
        logger.info("Cleaning up old NetBox comparison results.")

        # Delete all results older than 14 days
        NetboxOrthosComparisionRun.objects.filter(
            compare_timestamp__lt=datetime.datetime.now() - datetime.timedelta(days=14)
        ).delete()
