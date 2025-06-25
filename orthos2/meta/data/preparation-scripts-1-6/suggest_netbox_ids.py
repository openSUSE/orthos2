#!/usr/bin/python3

"""
This script will run on Orthos 2 Production with Git tag 1.5 and suggest NetBox IDs for Machines and Enclosures.
"""

from orthos2.data.models.enclosure import Enclosure
from orthos2.data.models.machine import Machine


def main() -> None:
    netbox_url = ""
    netbox_token = ""

    for machine in Machine.objects.all():
        # Cases
        # 1. Machine is independent --> No Parent device on NetBox
        # 2. Machine is enclosed in a multi-device chassis --> Parent device in Netbox --> Enclosure in Orthos 2 needs to be checked --> Check that all machines are in Netbox Parent Device/Orthos 2 Enclosure

        # Cases
        # 1. Machine FQDN can be found in the list of NetBox devices --> Suggest Device ID for machine
        # 2. Machine FQDN cannot be found in the list of NetBox devices --> Print error
        pass
