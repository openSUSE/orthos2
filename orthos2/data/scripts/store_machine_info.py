#!/usr/bin/python3
from typing import Any

from orthos2.taskmanager.tasks.ansible import Ansible


def run(*args: Any) -> None:

    if not args:
        print("Use --script-args to pass data.serverconfig.json file")
        exit(1)

    Ansible.store_machine_info(args[0])
