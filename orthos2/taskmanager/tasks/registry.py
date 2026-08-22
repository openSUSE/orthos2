"""
Authoritative list of schedulable `Task` subclasses, used to power the "Task" choice
field on `SingleTask`/`DailyTask` forms.

This is deliberately independent of the `__all__` re-exports in
`orthos2.taskmanager.tasks.__init__`, which exist purely as import convenience for
code that constructs and schedules tasks programmatically (e.g. `TaskManager.add()`
callers in `orthos2.data.signals`). `TaskExecuter.run()` resolves a queued task via
`importlib.import_module(basetask.module)` + `getattr(module, basetask.name)` against
the literal submodule path, so what matters here is that every listed class is a real,
importable `Task` subclass - not whether it happens to be re-exported from the package.
"""

from typing import List, Optional, Tuple, Type

from orthos2.taskmanager.models import Task
from orthos2.taskmanager.tasks.ansible import Ansible
from orthos2.taskmanager.tasks.cobbler import (
    RegenerateCobbler,
    SyncCobblerDHCP,
    UpdateCobblerMachine,
    UpdateCobblerRemotePowerDevice,
)
from orthos2.taskmanager.tasks.daily import (
    DailyCheckForPrimaryNetwork,
    DailyCheckReservationExpirations,
    DailyMachineChecks,
    DailyManufacturerDeviceTypeCleanup,
    DailyNetboxFetch,
)
from orthos2.taskmanager.tasks.machinetasks import MachineCheck, RegenerateMOTD
from orthos2.taskmanager.tasks.netbox import (
    NetboxCleanupComparisionResults,
    NetboxCompareDeviceType,
    NetboxCompareEnclosure,
    NetboxCompareFullMachine,
    NetboxCompareManufacturer,
    NetboxCompareRemotePowerDevice,
    NetboxFetchBMC,
    NetboxFetchDeviceType,
    NetboxFetchEnclosure,
    NetboxFetchFullDeviceType,
    NetboxFetchFullEnclosure,
    NetboxFetchFullMachine,
    NetboxFetchFullManufacturer,
    NetboxFetchMachine,
    NetboxFetchManufacturer,
    NetboxFetchNetworkInterface,
    NetboxFetchRemotePowerDevice,
)
from orthos2.taskmanager.tasks.notifications import (
    CheckForPrimaryNetwork,
    CheckMultipleAccounts,
    CheckReservationExpiration,
    SendReservationInformation,
    SendRestoredPassword,
)
from orthos2.taskmanager.tasks.sconsole import RegenerateSerialConsole
from orthos2.taskmanager.tasks.setup import SetupMachine
from orthos2.taskmanager.tasks.sol import DeactivateSerialOverLan

DAILY_TASK_CLASSES: List[Type[Task]] = [
    DailyMachineChecks,
    DailyCheckReservationExpirations,
    DailyCheckForPrimaryNetwork,
    DailyNetboxFetch,
    DailyManufacturerDeviceTypeCleanup,
]
"""
Tasks intended to run on a recurring daily schedule (see `orthos2.taskmanager.tasks.daily`) -
each fans out into one-off tasks via `TaskManager.add()` rather than doing work directly.
The only tasks selectable via the `DailyTask` "Task" choice field.
"""

SINGLE_TASK_CLASSES: List[Type[Task]] = [
    Ansible,
    RegenerateCobbler,
    UpdateCobblerMachine,
    UpdateCobblerRemotePowerDevice,
    SyncCobblerDHCP,
    MachineCheck,
    RegenerateMOTD,
    NetboxFetchEnclosure,
    NetboxFetchMachine,
    NetboxFetchBMC,
    NetboxFetchNetworkInterface,
    NetboxFetchManufacturer,
    NetboxFetchDeviceType,
    NetboxFetchRemotePowerDevice,
    NetboxFetchFullMachine,
    NetboxFetchFullEnclosure,
    NetboxFetchFullManufacturer,
    NetboxFetchFullDeviceType,
    NetboxCompareFullMachine,
    NetboxCompareEnclosure,
    NetboxCompareManufacturer,
    NetboxCompareDeviceType,
    NetboxCompareRemotePowerDevice,
    NetboxCleanupComparisionResults,
    SendRestoredPassword,
    SendReservationInformation,
    CheckReservationExpiration,
    CheckMultipleAccounts,
    CheckForPrimaryNetwork,
    RegenerateSerialConsole,
    SetupMachine,
    DeactivateSerialOverLan,
]
"""
Every one-off task, i.e. every `Task` subclass except the daily-schedule orchestrators
in `DAILY_TASK_CLASSES` above. The only tasks selectable via the `SingleTask` "Task"
choice field.
"""

TASK_CLASSES: List[Type[Task]] = DAILY_TASK_CLASSES + SINGLE_TASK_CLASSES
"""Every known `Task` subclass, regardless of type - the full inventory."""


def task_value(cls: Type[Task]) -> str:
    """Return the dotted `module.ClassName` value stored on a task's `module`+`name`."""
    return "{}.{}".format(cls.__module__, cls.__name__)


def task_label(cls: Type[Task]) -> str:
    """Return a short, human-readable label for a task class."""
    return "{}.{}".format(cls.__module__.rsplit(".", 1)[-1], cls.__name__)


def _choices(classes: List[Type[Task]]) -> List[Tuple[str, str]]:
    return sorted(
        ((task_value(cls), task_label(cls)) for cls in classes),
        key=lambda choice: choice[1],
    )


def _resolve(value: str, classes: List[Type[Task]]) -> Optional[Tuple[str, str]]:
    valid_values = {task_value(cls) for cls in classes}
    if value not in valid_values:
        return None
    return tuple(value.rsplit(".", 1))  # type: ignore[return-value]


def task_choices() -> List[Tuple[str, str]]:
    """Return sorted (value, label) choices for every one-off task class."""
    return _choices(SINGLE_TASK_CLASSES)


def resolve_task_value(value: str) -> Optional[Tuple[str, str]]:
    """Split a selected `task` choice value into its `(module, name)` pair, or return None if unknown."""
    return _resolve(value, SINGLE_TASK_CLASSES)


def daily_task_choices() -> List[Tuple[str, str]]:
    """Return sorted (value, label) choices for tasks meant to run on a recurring schedule."""
    return _choices(DAILY_TASK_CLASSES)


def resolve_daily_task_value(value: str) -> Optional[Tuple[str, str]]:
    """Split a selected daily `task` choice value into `(module, name)`, or return None if unknown."""
    return _resolve(value, DAILY_TASK_CLASSES)
