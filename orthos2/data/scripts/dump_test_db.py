#!/usr/bin/python3

import os

from django.apps import apps
from orthos2.data.models.domain import Domain, DomainAdmin
from orthos2.data.models.machine import Machine

"""
Usage:
First Parameters: Tables to dump [general|<domain>|...]
Second Paramter: "natural" Use natural primary/foreign keys (default)

                 "pk" to dump Primary/Foreign keys with numbers
                 (only works if loaded into a freshly installed database)

Examples:
manage runscript dump_test_db  --script-args general
manage runscript dump_test_db  --script-args test-30.arch.suse.de

Also see: https://docs.djangoproject.com/en/3.2/topics/serialization
"""

Modules = {}

Modules['general'] = ( "Serverconfig", "System", "Architecture", "Vendor", "Platform" )

Modules['domain'] = ( "Domain", "Domainadmin" )

Modules['remote' ] = ( "Remotepower", "Bmc", "Remotepowerdevice", "Serialconsole", "Serialconsoletype" )

queries = []

added_machines = []

config = apps.get_app_config("data")

def show_help():
    print("Use --script-args to specify what you want to dump:")
    print("")
    print("\tgeneral \t-- Dump general DB data [ %s ] " % ", ".join(Modules['general']))
    print("")
    print("\tremote  \t-- Dump remote management HW DB data [ %s ] " % ", ".join(Modules['remote']))
    print("")
    print("\t<domain>\t-- Dump data of a specific domain [ %s ] " % ", ".join(Modules['domain']))
    print()
    print("Examples:")
    print("manage runscript dump_test_db  --script-args=general")
    print("manage runscript dump_test_db  --script-args=test-30.arch.suse.de")
    print()
    print("First Parameters: Tables to dump [general|<domain>|...]")
    print("Second Paramter: \"natural\" Use natural primary/foreign keys (default)")
    print("                 \"pk\" to dump Primary/Foreign keys with numbers")
    print("                  (only works if loaded into a freshly installed database)")

    exit(1)

def add_machine(fqdn: str, queries: list):

    if fqdn in added_machines:
        # already added
        print("Machine already added: %s" % fqdn)
        return
    try:
        machine = Machine.objects.get(fqdn=fqdn)
        query = Machine.objects.filter(fqdn=fqdn)
        queries.extend(query)
        if machine.hypervisor:
            add_machine(machine.hypervisor.fqdn, queries)
    except Machine.DoesNotExist:
        print("%s - Machine does not exist" % fqdn)
        show_help()
    added_machines.append(fqdn)

def add_domain(domain :str, queries : list):

    try:
        domain = Domain.objects.get(name=domain)
        query = Domain.objects.filter(name=domain)
        queries.extend(query)
        query = DomainAdmin.objects.filter(domain=domain)
        queries.extend(query)
    except Domain.DoesNotExist:
        print("%s - Domain does not exist" % domain)
        show_help()

    if domain.tftp_server:
        add_machine(domain.tftp_server.fqdn, queries)
    if domain.cscreen_server:
        add_machine(domain.cscreen_server.fqdn, queries)
    if domain.cobbler_server and len(domain.cobbler_server.all()):
        add_machine(domain.cobbler_server.all()[0].fqdn, queries)

    print("Adding domain %s" % domain)
    print("Adding %d machines related machines: %s" % (len(added_machines), added_machines))

    
def run(*args):

    natural = True

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

    param = args[0]
    tables = Modules.get(param)

    if not tables:
        add_domain(param, queries)
    else:
        for table in tables:
            print (".. dump table %s" % table)
            model = config.get_model(table).objects.all()
            queries.extend(model)

    file = param + ".json"
    print(queries)
    with open(file, "w") as out:
        from django.core import serializers
        serializers.serialize("json", queries, indent=2, stream=out, use_natural_foreign_keys=natural,use_natural_primary_keys=natural)
        print("File dumped: %s" % os.path.abspath(file))
