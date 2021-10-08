#!/usr/bin/python3

import os

from django.apps import apps
from django.core import serializers
from orthos2.data import models
from django.db import DEFAULT_DB_ALIAS
from rest_framework.serializers import ModelSerializer
import rest_framework

      

Modules = {}

Modules['general'] = ( "Serverconfig", "System", "Architecture", "Vendor", "Platform" )

Modules['domain'] = ( "Domain", "Domainadmin" )

Modules['remote' ] = ( "Remotepower", "Bmc", "Remotepowerdevice", "Serialconsole", "Serialconsoletype" )

queries = []

config = apps.get_app_config("data")

def help():
    print("Use --script-args to specify what you want to dump:")
    print("")
    print("\tgeneral \t-- Dump general DB data [ %s ] " % ", ".join(Modules['general']))
    print("")
    print("\tremote  \t-- Dump remote management HW DB data [ %s ] " % ", ".join(Modules['remote']))
    print("")
    print("\t<domain>\t-- Dump data of a specific domain [ %s ] " % ", ".join(Modules['domain']))
    exit(1)

def add_domain(domain :str, queries : list):

    try:
        domain = config.get_model("Domain").objects.get(name=domain)
        query = config.get_model("Domain").objects.filter(name=domain)
        queries.extend(query)
        if domain.tftp_server:
            query = config.get_model("Machine").objects.filter(pk=domain.tftp_server.pk)
            queries.extend(query)
        if domain.cscreen_server:
            query = config.get_model("Machine").objects.filter(pk=domain.cscreen_server.pk)
            queries.extend(query)
        if domain.cobbler_server:
            query = domain.cobbler_server.all()
            queries.extend(query)
            
    except models.domain.Domain.DoesNotExist:
        print("%s - Domain does not exist" % domain)
        help()

    if domain:
        print(domain)
    else:
        print("No domain found")
        help()


    
def run(*args):
    
    if not args or args[0] == "help":
        help()
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
    print("Dumping to file: %s" % os.path.abspath(file))
    print(queries)
    out = open(file, "w")
    from django.core import serializers
    serializers.serialize("json", queries, indent=2, stream=out)
    out.close()

