#!/usr/bin/python3

import os

from django.apps import apps
from django.core.management.base import BaseCommand

from orthos2.data.models.domain import Domain, DomainAdmin
from orthos2.data.models.machine import Enclosure, Machine, NetworkInterface
from orthos2.taskmanager.models import DailyTask

USAGE = """
Usage:
First Parameters: Tables to dump [general|<domain>|...]
Second Paramter: "pk" to dump Primary/Foreign keys with numbers (default)
                 (only works if loaded into a freshly installed database)

                 "natural" Use natural primary/foreign keys
                 Could also work for already existing databases, but is not
                 fully implemented yet

Examples:
manage dump_db
manage dump_db arch.suse.cz
...

scp /var/lib/orthos2/{test-30.arch.suse.de.json,general.json} <orthos2-testserver.arch.suse.de>:/tmp

ssh root@orthos2-testserver.arch.suse.de

rm /var/lib/orthos2/database/db.sqlite3
manage migrate
manage createsuperuser
manage loaddata /tmp/general
manage loaddata /tmp/test-30.arch.suse.de
...

Also see: https://docs.djangoproject.com/en/3.2/topics/serialization
"""

Modules = {}

# General also includes taskmanager.dailytask and basic arch.suse.de domain
Modules["general"] = (
    "Serverconfig",
    "System",
    "Architecture",
    "Vendor",
    "Platform",
    "Serialconsoletype",
)

Modules["domain"] = ("Domain", "Domainadmin")

# Modules['remote' ] = ( "Remotepower", "Bmc", "Remotepowerdevice", "Serialconsole", "Serialconsoletype" )

added_machines = []
domains = [
    "test-100.arch.suse.de",
    "test-10.arch.suse.de",
    "test-20.arch.suse.de",
    "test-30.arch.suse.de",
    "test-40.arch.suse.de",
    "devlab.prv.suse.com",
]


def show_help():
    print("Use --script-args to specify what you want to dump:")
    print("")
    print("\tgeneral \t-- Dump general DB data [ %s ] " % ", ".join(Modules["general"]))
    print("")
    # print("\tremote  \t-- Dump remote management HW DB data [ %s ] " % ", ".join(Modules['remote']))
    # print("")
    print(
        "\t<domain>\t-- Dump data of a specific domain [ %s ] "
        % ", ".join(Modules["domain"])
    )
    print()
    print(USAGE)
    exit(1)


class Command(BaseCommand):
    help = "Dump orthos DB data\n"
    help += USAGE

    config = apps.get_app_config("data")
    queries = []

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.machinesonly = False

    def add_machine(self, fqdn: str):
        if fqdn in added_machines:
            # already added
            print("Machine already added: %s" % fqdn)
            return
        try:
            machine = Machine.objects.get(fqdn=fqdn)
            query = Enclosure.objects.filter(pk=machine.enclosure.pk)
            self.queries.extend(query)
            query = Machine.objects.filter(fqdn=fqdn)
            self.queries.extend(query)
            if machine.hypervisor:
                self.add_machine(machine.hypervisor.fqdn)
            added_machines.append(fqdn)
        except Machine.DoesNotExist:
            print("%s - Machine does not exist" % fqdn)
            show_help()

    def add_domain_infra(self, domain: str):
        try:
            """
            This is needed if we want to have a blank domain with
            only tftp, cobbler and cscreen server relations
            """
            d_obj = Domain.objects.get(name=domain)
            if d_obj.tftp_server:
                self.add_machine(d_obj.tftp_server.fqdn)
            if d_obj.cscreen_server:
                self.add_machine(d_obj.cscreen_server.fqdn)
            if d_obj.cobbler_server:
                self.add_machine(d_obj.cobbler_server.fqdn)

            query = Domain.objects.filter(name=d_obj)
            self.queries.extend(query)
            query = DomainAdmin.objects.filter(domain=d_obj)
            self.queries.extend(query)
        except Domain.DoesNotExist:
            print("%s - Domain does not exist" % domain)
            show_help()

    def add_domain_machines(self, domain: str):
        machines = Machine.objects.filter(fqdn_domain__name=domain)
        for machine in machines:
            self.add_machine(machine)

    def add_arch_relations(self):
        """
        We always need arch.suse.de domain and markeb.arch.suse.de
        We delete unneeded machine references
        """
        query = Domain.objects.filter(name="arch.suse.de")
        for item in query:
            item.tftp_server = None
            item.cscreen_server = None
            item.cobbler_server = None
        self.queries.extend(query)
        self.add_machine("markeb.arch.suse.de")

    def delete_network(mac: str):
        network = NetworkInterface.objects.get(mac_address=mac.upper())
        if network:
            print(network)
            network.delete()
        exit(1)

    def add_arguments(self, parser):
        parser.add_argument(
            "domain", nargs="*", default=domains, help="Dump domain tables"
        )
        parser.add_argument(
            "--natural",
            action="store_true",
            help="Store natural PK keys",
            default=False,
        )
        parser.add_argument(
            "--filename", default="db_dump", help="Dump tables filename.json"
        )
        group = parser.add_mutually_exclusive_group()
        group.add_argument(
            "--machinesonly",
            action="store_true",
            help="Dump only systems/machines of specified domains",
        )
        group.add_argument(
            "--general",
            action="store_true",
            help="Store general DB metadata",
            default=False,
        )

    def handle(self, *args, **options):

        self.natural = False
        # delete_network('00:01:73:02:37:74')
        filename = "db_dump"
        # whitespace separated domains passed as one argument
        domains = options["domain"]
        filename = options["filename"]
        self.file = filename + ".json"
        self.machinesonly = options["machinesonly"]
        self.general = options["general"]

        if self.general:
            tables = Modules.get("general")
            self.add_arch_relations()
            query = DailyTask.objects.all()
            if query:
                self.queries.extend(query)
            for table in tables:
                print(".. dump table %s" % table)
                model = self.config.get_model(table).objects.all()
                self.queries.extend(model)

        for domain in domains:
            print("Adding domain: %s" % domain)
            if not self.machinesonly:
                self.add_domain_infra(domain)
            self.add_domain_machines(domain)

        self.save()

    def save(self):
        # print(queries)
        with open(self.file, "w") as out:
            from django.core import serializers

            serializers.serialize(
                "json",
                self.queries,
                indent=2,
                stream=out,
                use_natural_foreign_keys=self.natural,
                use_natural_primary_keys=self.natural,
            )
            print("File dumped: %s" % os.path.abspath(self.file))
