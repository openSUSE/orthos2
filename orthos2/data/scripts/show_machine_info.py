#!/usr/bin/python3

from orthos2.taskmanager.tasks.ansible import Ansible


def run(*args):

    if not args:
        print("Use --script-args to pass data.serverconfig.json file")
        exit(1)

    Ansible.print_machine_info(args[0])
