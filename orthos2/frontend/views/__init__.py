"""
This module contains all Django frontend views. For convenience, they are all reexported.
"""

from .ajax import annotation, powercycle, virtualization_delete, virtualization_list
from .auth import deprecate_current_app, login
from .compare_netbox import (
    NetboxOrthosComparisionRunListView,
    netboxorthoscomparisonrun,
)
from .machine import (
    compare_netbox,
    console,
    cpu,
    fetch_netbox,
    history,
    installations,
    machine,
    machine_add,
    machine_netboxcomparision,
    machine_release,
    machine_reserve,
    misc,
    networkinterfaces,
    pci,
    rescan,
    scsi,
    setup,
    usb,
    virtualization,
    virtualization_add,
)
from .machines import (
    AllMachineListView,
    FreeMachineListView,
    MachineListView,
    MyMachineListView,
    VirtualMachineListView,
    machine_search,
)
from .regenerate import (
    regenerate_cobbler,
    regenerate_domain_cobbler,
    regenerate_domain_cscreen,
    regenerate_machine_cobbler,
    regenerate_machine_motd,
)
from .statistics import statistics
from .user import users_create, users_password_restore, users_preferences

__all__ = [
    "annotation",
    "powercycle",
    "virtualization_list",
    "virtualization_delete",
    "deprecate_current_app",
    "login",
    "NetboxOrthosComparisionRunListView",
    "netboxorthoscomparisonrun",
    "pci",
    "cpu",
    "networkinterfaces",
    "installations",
    "usb",
    "scsi",
    "virtualization",
    "virtualization_add",
    "misc",
    "machine_reserve",
    "machine_release",
    "history",
    "rescan",
    "setup",
    "console",
    "machine",
    "machine_netboxcomparision",
    "fetch_netbox",
    "compare_netbox",
    "machine_add",
    "MachineListView",
    "AllMachineListView",
    "MyMachineListView",
    "FreeMachineListView",
    "VirtualMachineListView",
    "machine_search",
    "regenerate_cobbler",
    "regenerate_domain_cscreen",
    "regenerate_domain_cobbler",
    "regenerate_machine_motd",
    "regenerate_machine_cobbler",
    "statistics",
    "users_create",
    "users_password_restore",
    "users_preferences",
]
