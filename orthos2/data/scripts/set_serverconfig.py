#!/usr/bin/python3
#
# Script to override current ServerConfig variables with a
# (can also be a subset of) json formatted database dump of
# the ServerConfig table
# Obtain the dump via:
# sudo -u orthos /usr/lib/orthos2/manage.py dumpdata --indent 2 data.serverconfig >/tmp/data.serverconfig.json
#
# Usage of this script:
# sudo -u orthos /usr/lib/orthos2/manage.py runscript set_serverconfig --script-args /tmp/data.serverconfig.json
#


import json
from orthos2.data.models.serverconfig import ServerConfig


def run(*args):
    if not args:
        print("Use --script-args to pass data.serverconfig.json file")
        exit(1)

    with open(args[0], 'r') as json_file:
        serverconf = json.load(json_file)

    db_serverconf = ServerConfig.objects.all()

    for entry in serverconf:
        key = entry['fields'].get('key')
        value = entry['fields'].get('value')
        db_obj = db_serverconf.get(key=key)
        if not db_obj:
            print("Key {} does not exist in server config".format(key))
            exit(1)

        old_val = db_obj.value
        if old_val == value:
            continue
        else:
            db_obj.value = value
            db_obj.save()
            print("{key} updated:".format(key=key))
            print("{old_val}  -->>  {value}".format(old_val=old_val, value=value))
