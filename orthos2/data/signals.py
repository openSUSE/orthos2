import logging
import os
import time
from typing import Any, Optional

from django.db.models.signals import post_delete, post_save, pre_delete
from django.dispatch import Signal, receiver

from orthos2.data.models import Machine, SerialConsole, ServerConfig
from orthos2.taskmanager import tasks
from orthos2.taskmanager.models import TaskManager
from orthos2.utils.cobbler import CobblerServer
from orthos2.utils.misc import Serializer

logger = logging.getLogger("orthos")


signal_cobbler_regenerate = Signal()
signal_cobbler_sync_dhcp = Signal()
signal_cobbler_machine_update = Signal()
signal_serialconsole_regenerate = Signal()
signal_motd_regenerate = Signal()


@receiver(pre_delete, sender=Machine)
def machine_pre_delete(
    sender: Any, instance: Machine, *args: Any, **kwargs: Any
) -> None:
    """Pre delete action for machine. Save deleted machine object as file for archiving.
    Also remove the machine from the cobbler Server.
    """
    server = CobblerServer(instance.fqdn_domain)
    if server:
        server.remove(instance)

    if instance.is_vm_managed():
        instance.hypervisor.virtualization_api.remove(instance)  # type: ignore

    if not ServerConfig.get_server_config_manager().bool_by_key(
        "serialization.execute"
    ):
        return

    output_format = ServerConfig.get_server_config_manager().by_key(
        "serialization.output.format"
    )

    if output_format is None:
        logger.warning(
            "No output format configured. Use 'json' for serialization output format..."
        )
        output_format = Serializer.Format.JSON

    output_directory = ServerConfig.get_server_config_manager().by_key(
        "serialization.output.directory"
    )

    if output_directory is None:
        logger.warning(
            "No output directory configured. Use '/tmp' for serialization output..."
        )
        output_directory = "/tmp"

    if not os.access(output_directory, os.W_OK):
        logger.warning(
            "Target directory '%s' does not exist/is not writeable!", output_directory
        )
        output_directory = "/tmp"

    serialized_data, output_format = instance.serialize(output_format=output_format)

    filename = "{}/{}-{}.{}".format(
        output_directory.rstrip("/"), instance.fqdn, str(time.time()), output_format
    )

    with open(filename, "w") as machine_description:
        machine_description.write(serialized_data)

    logger.info("Machine object serialized (target: '%s')", filename)


@receiver(post_save, sender=SerialConsole)
def serialconsole_post_save(
    sender: Any, instance: SerialConsole, *args: Any, **kwargs: Any
) -> None:
    """Regenerate cscreen server configs if a serial console info got changed"""
    if not instance.machine.fqdn_domain.cscreen_server:
        return
    signal_serialconsole_regenerate.send(  # type: ignore
        sender=SerialConsole,
        cscreen_server_fqdn=instance.machine.fqdn_domain.cscreen_server.fqdn,
    )


@receiver(post_delete, sender=SerialConsole)
def serialconsole_post_delete(
    sender: Any, instance: SerialConsole, *args: Any, **kwargs: Any
) -> None:
    """Regenerate cscreen server configs if a serial console got deleted"""
    if not instance.machine.fqdn_domain.cscreen_server:
        return
    signal_serialconsole_regenerate.send(  # type: ignore
        sender=SerialConsole,
        cscreen_server_fqdn=instance.machine.fqdn_domain.cscreen_server.fqdn,
    )


@receiver(signal_serialconsole_regenerate)
def regenerate_serialconsole(
    sender: Any, cscreen_server_fqdn: str, *args: Any, **kwargs: Any
) -> None:
    """
    Create `RegenerateSerialConsole()` task here.

    This should be the one and only place for creating this task.
    """
    if cscreen_server_fqdn is not None:  # type: ignore[reportUnnecessaryComparison]
        task = tasks.RegenerateSerialConsole(cscreen_server_fqdn)
        TaskManager.add(task)


@receiver(signal_cobbler_regenerate)
def regenerate_cobbler(
    sender: Any, domain_id: Optional[int], *args: Any, **kwargs: Any
) -> None:
    """
    Create `RegenerateCobbler()` task here.

    This should be the one and only place for creating this task.
    """
    if domain_id is None:
        task = tasks.RegenerateCobbler()
    else:
        task = tasks.RegenerateCobbler(domain_id)

    TaskManager.add(task)


@receiver(signal_cobbler_sync_dhcp)
def cobbler_sync_dhcp(sender: Any, domain_id: int, *args: Any, **kwargs: Any) -> None:
    """
    Create `RegenerateCobbler()` task here.

    This should be the one and only place for creating this task.
    """
    task = tasks.SyncCobblerDHCP(domain_id)
    TaskManager.add(task)


@receiver(signal_cobbler_machine_update)
def update_cobbler_machine(
    sender: Any, domain_id: int, machine_id: int, *args: Any, **kwargs: Any
) -> None:
    """
    Create `RegenerateCobbler()` task here.

    This should be the one and only place for creating this task.
    """
    task = tasks.UpdateCobblerMachine(domain_id, machine_id)
    TaskManager.add(task)


@receiver(signal_motd_regenerate)
def regenerate_motd(sender: Any, fqdn: str, *args: Any, **kwargs: Any) -> None:
    """
    Create `RegenerateMOTD()` task here.

    This should be the one and only place for creating this task.
    """
    task = tasks.RegenerateMOTD(fqdn)
    TaskManager.add(task)
