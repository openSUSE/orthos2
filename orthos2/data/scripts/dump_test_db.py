#!/usr/bin/python3

import os
from typing import Any, List

from django.apps import apps

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
manage runscript dump_test_db  --script-args general
manage runscript dump_test_db  --script-args test-30.arch.suse.de
manage runscript dump_test_db  --script-args test-100.arch.suse.de
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

Modules["domain"] = ("Domain", "Domainadmin")  # type: ignore

# Modules['remote' ] = ("Remotepower", "Bmc", "Remotepowerdevice", "Serialconsole", "Serialconsoletype")

queries = []  # type: ignore

added_machines: List[str] = []

config = apps.get_app_config("data")


def show_help() -> None:
    print("Use --script-args to specify what you want to dump:")
    print("")
    modules = ", ".join(Modules["general"])  # type: ignore
    print("\tgeneral \t-- Dump general DB data [ %s ] " % modules)
    print("")
    # print("\tremote  \t-- Dump remote management HW DB data [ %s ] " % ", ".join(Modules['remote']))
    # print("")
    print(
        "\t<domain>\t-- Dump data of a specific domain [ %s ] "
        % ", ".join(Modules["domain"])  # type: ignore
    )
    print()
    print(USAGE)
    exit(1)


def add_machine(fqdn: str, queries: List[Any]):

    if fqdn in added_machines:
        # already added
        print("Machine already added: %s" % fqdn)
        return
    try:
        machine = Machine.objects.get(fqdn=fqdn)
        queries.extend(Enclosure.objects.filter(pk=machine.enclosure.pk))
        queries.extend(Machine.objects.filter(fqdn=fqdn))
        if machine.hypervisor:
            add_machine(machine.hypervisor.fqdn, queries)
    except Machine.DoesNotExist:
        print("%s - Machine does not exist" % fqdn)
        show_help()
    added_machines.append(fqdn)


def add_domain(domain: str, queries: List[Any]) -> None:

    try:
        """
        This is needed if we want to have a blank domain with
        only tftp, cobbler and cscreen server relations
        """

        d_obj = Domain.objects.get(name=domain)
        if d_obj.tftp_server:
            add_machine(d_obj.tftp_server.fqdn, queries)
        if d_obj.cscreen_server:
            add_machine(d_obj.cscreen_server.fqdn, queries)
        if d_obj.cobbler_server:
            add_machine(d_obj.cobbler_server.fqdn, queries)

        queries.extend(Domain.objects.filter(name=d_obj))
        queries.extend(DomainAdmin.objects.filter(domain=d_obj))
    except Domain.DoesNotExist:
        print("%s - Domain does not exist" % domain)
        show_help()


def add_arch_relations(queries: List[Any]):
    """
    We always need arch.suse.de domain and markeb.arch.suse.de
    We delete unneeded machine references
    """
    query = Domain.objects.filter(name="arch.suse.de")
    for item in query:
        item.tftp_server = None
        item.cscreen_server = None
        item.cobbler_server = None
    queries.extend(query)
    add_machine("markeb.arch.suse.de", queries)


def delete_network(mac: str) -> None:
    network = NetworkInterface.objects.get(mac_address=mac.upper())
    if network:
        print(network)
        network.delete()
    exit(1)


def run(*args: Any):

    natural = False
    # delete_network('00:01:73:02:37:74')
    if not args or args[0] == "help" or len(args) > 2:
        show_help()

    if len(args) == 2:
        if args[1] == "pk":
            print("Using numbers as Primary/Foreign keys")
            natural = False
        elif args[1] == "natural":
            print("Using natural keys as Primary/Foreign keys")
            natural = True
        else:
            show_help()

    param = args[0]  # type: ignore
    tables = Modules.get(param)  # type: ignore

    if not tables:
        add_domain(param, queries)  # type: ignore
    else:
        add_arch_relations(queries)  # type: ignore
        query = DailyTask.objects.all()
        if query:
            queries.extend(query)  # type: ignore
        for table in tables:  # type: ignore
            print(".. dump table %s" % table)  # type: ignore
            model = config.get_model(table).objects.all()  # type: ignore
            queries.extend(model)  # type: ignore

    file = param + ".json"
    # print(queries)
    with open(file, "w") as out:
        from django.core import serializers

        serializers.serialize(
            "json",
            queries,  # type: ignore
            indent=2,
            stream=out,
            use_natural_foreign_keys=natural,
            use_natural_primary_keys=natural,
        )
        print("File dumped: %s" % os.path.abspath(file))
