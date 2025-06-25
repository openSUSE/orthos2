"""
This Django management command will suggest NetBox IDs for Machines and Enclosures.
"""
from django.core.management import BaseCommand

from orthos2 import settings
from orthos2.data.models.enclosure import Enclosure
from orthos2.data.models.machine import Machine


class Command(BaseCommand):
    help = "Suggest NetBox IDs for Machines and Enclosures in Orthos 2."

    def handle(self, *args, **options):
        """
        Entrypoint for Django to execute the management command.
        """
        netbox_url = settings.NETBOX_URL
        netbox_token = settings.NETBOX_TOKEN

        for machine in Machine.objects.all():
            # Cases
            # 1. Machine is independent --> No Parent device on NetBox
            # 2. Machine is enclosed in a multi-device chassis --> Parent device in Netbox --> Enclosure in Orthos 2 needs to be checked --> Check that all machines are in Netbox Parent Device/Orthos 2 Enclosure

            # Cases
            # 1. Machine FQDN can be found in the list of NetBox devices --> Suggest Device ID for machine
            # 2. Machine FQDN cannot be found in the list of NetBox devices --> Print error
            pass
