import logging
import os
import time

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.models.signals import (post_delete, post_init, post_save,
                                      pre_delete, pre_save)
from django.dispatch import Signal, receiver
from orthos2.taskmanager import tasks
from orthos2.taskmanager.models import TaskManager
from orthos2.utils.misc import (Serializer, get_hostname, is_dns_resolvable,
                                is_valid_mac_address)
from orthos2.utils.cobbler import CobblerServer

from .exceptions import HostnameNotDnsResolvable
from .models import (Enclosure, Machine, NetworkInterface, RemotePower,
                     SerialConsole, ServerConfig, System,
                     is_unique_mac_address, validate_dns, validate_mac_address)
logger = logging.getLogger('orthos')


signal_cobbler_regenerate = Signal(providing_args=['domain_id'])
signal_cobbler_machine_update = Signal(providing_args=['domain_id', 'machine_id'])
signal_serialconsole_regenerate = Signal(providing_args=['cscreen_server_fqdn'])
signal_motd_regenerate = Signal(providing_args=['fqdn'])

@receiver(pre_save, sender=Machine)
def machine_pre_save(sender, instance, *args, **kwargs):
    """Prevent saving machine object if MAC address is already in use (exclude own interfaces)."""
    if hasattr(instance, 'networkinterfaces'):
        exclude = instance.networkinterfaces.all().values_list('mac_address', flat=True)
    else:
        exclude = []

    if not is_unique_mac_address(instance.mac_address, exclude=exclude):
        raise ValidationError(
            "MAC address '{}' is already used by '{}'!".format(
                instance.mac_address,
                NetworkInterface.objects.get(mac_address=instance.mac_address).machine.fqdn
            )
        )


@receiver(post_save, sender=Machine)
def machine_post_save(sender, instance, *args, **kwargs):
    """
    Post action after machine is saved.

    When a machine gets added, the primary (initial) network interface gets added. If the MAC
    address changed for primary network interface, a new primary network interface gets added
    whereas the other network interfaces remain.

    Systems with 'administrative' flag set do only get one single network interface.
    """
    if not instance.mac_address:
        return

    try:
        primary_networkinterface = NetworkInterface.objects.get(machine=instance, primary=True)
    except ObjectDoesNotExist:
        primary_networkinterface = None
    if primary_networkinterface:
        if primary_networkinterface.mac_address.upper() != instance.mac_address.upper():

            networkinterface, created = instance.networkinterfaces.get_or_create(
                machine=instance,
                mac_address=instance.mac_address
            )

            networkinterface.primary = True
            networkinterface.mac_address = instance.mac_address

            primary_networkinterface.primary = False
            primary_networkinterface.save()

            networkinterface.save()

            if instance.system.administrative:
                primary_networkinterface.delete()
            else:
                # scan networkinterfaces
                instance.scan('networkinterfaces')
                # regenerate Cobbler entry
                signal_cobbler_regenerate.send(sender=None, domain_id=instance.fqdn_domain.pk)
    else:
        instance.networkinterfaces.create(
            machine=instance,
            primary=True,
            mac_address=instance.mac_address
        )
        instance.scan('networkinterfaces')
          # create Cobbler entry
        signal_cobbler_regenerate.send(sender=None, domain_id=instance.fqdn_domain.pk)





@receiver(post_init, sender=Machine)
def machine_post_init(sender, instance, *args, **kwargs):
    """Post init action for machine. Set non-database saved values here."""
    if instance.pk:
        try:
            instance.hostname = get_hostname(instance.fqdn)

            if instance.get_primary_networkinterface():
                instance.mac_address = instance.get_primary_networkinterface().mac_address
        except Exception as e:
            logger.warning("Errors occurred during machine init: '{}': {}".format(instance, e))


@receiver(pre_delete, sender=Machine)
def machine_pre_delete(sender, instance, *args, **kwargs):
    """Pre delete action for machine. Save deleted machine object as file for archiving.
       Also remove the machine from the cobbler Server.
    """
    server = CobblerServer.from_machine(instance)
    if server:
        server.remove(instance)

    if instance.is_vm_managed():
        instance.hypervisor.virtualization_api.remove(machine)

    if not ServerConfig.objects.bool_by_key('serialization.execute'):
        return

    output_format = ServerConfig.objects.by_key('serialization.output.format')

    if output_format is None:
        logger.warning("No output format configured. Use 'json' for serialization output format...")
        output_format = Serializer.Format.JSON

    output_directory = ServerConfig.objects.by_key('serialization.output.directory')

    if output_directory is None:
        logger.warning("No output directory configured. Use '/tmp' for serialization output...")
        output_directory = '/tmp'

    if not os.access(output_directory, os.W_OK):
        logger.warning("Target directory '{}' does not exist/is not writeable!".format(
            output_directory
        ))
        output_directory = '/tmp'

    serialized_data, output_format = instance.serialize(output_format=output_format)

    filename = '{}/{}-{}.{}'.format(
        output_directory.rstrip('/'),
        instance.fqdn,
        str(time.time()),
        output_format
    )

    with open(filename, 'w') as machine_description:
        machine_description.write(serialized_data)

    logger.info("Machine object serialized (target: '{}')".format(filename))


@receiver(post_save, sender=SerialConsole)
def serialconsole_post_save(sender, instance, *args, **kwargs):
    signal_serialconsole_regenerate.send(
        sender=SerialConsole,
        cscreen_server_fqdn=instance.machine.fqdn_domain.cscreen_server.fqdn
    )


@receiver(post_delete, sender=SerialConsole)
def serialconsole_post_delete(sender, instance, *args, **kwargs):

    signal_serialconsole_regenerate.send(
        sender=SerialConsole,
        cscreen_server_fqdn=instance.machine.fqdn_domain.cscreen_server.fqdn
    )


@receiver(signal_serialconsole_regenerate)
def regenerate_serialconsole(sender, cscreen_server_fqdn, *args, **kwargs):
    """
    Create `RegenerateSerialConsole()` task here.

    This should be the one and only place for creating this task.
    """
    if cscreen_server_fqdn is not None:
        task = tasks.RegenerateSerialConsole(cscreen_server_fqdn)
        TaskManager.add(task)


@receiver(signal_cobbler_regenerate)
def regenerate_cobbler(sender, domain_id, *args, **kwargs):
    """
    Create `RegenerateCobbler()` task here.

    This should be the one and only place for creating this task.
    """
    if domain_id is None:
        task = tasks.RegenerateCobbler()
    else:
        task = tasks.RegenerateCobbler(domain_id)

    TaskManager.add(task)


@receiver(signal_cobbler_machine_update)
def update_cobbler_machine(sender, domain_id, machine_id, *args, **kwargs):
    """
    Create `RegenerateCobbler()` task here.

    This should be the one and only place for creating this task.
    """
    task = tasks.UpdateCobblerMachine(domain_id, machine_id)
    TaskManager.add(task)


@receiver(signal_motd_regenerate)
def regenerate_motd(sender, fqdn, *args, **kwargs):
    """
    Create `RegenerateMOTD()` task here.

    This should be the one and only place for creating this task.
    """
    task = tasks.RegenerateMOTD(fqdn)
    TaskManager.add(task)
