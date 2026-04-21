from .cobbler import (
    RegenerateCobbler,
    SyncCobblerDHCP,
    UpdateCobblerMachine,
    UpdateCobblerRemotePowerDevice,
)
from .daily import (
    DailyCheckForPrimaryNetwork,
    DailyCheckReservationExpirations,
    DailyMachineChecks,
)
from .machinetasks import MachineCheck, RegenerateMOTD
from .netbox import (
    NetboxCleanupComparisionResults,
    NetboxCompareEnclosure,
    NetboxCompareFullMachine,
    NetboxCompareRemotePowerDevice,
    NetboxFetchBMC,
    NetboxFetchEnclosure,
    NetboxFetchFullEnclosure,
    NetboxFetchFullMachine,
    NetboxFetchMachine,
    NetboxFetchNetworkInterface,
    NetboxFetchRemotePowerDevice,
)
from .notifications import (
    CheckForPrimaryNetwork,
    CheckMultipleAccounts,
    CheckReservationExpiration,
    SendReservationInformation,
    SendRestoredPassword,
)
from .sconsole import RegenerateSerialConsole
from .setup import SetupMachine
from .sol import DeactivateSerialOverLan

__all__ = [
    "CheckForPrimaryNetwork",
    "CheckMultipleAccounts",
    "CheckReservationExpiration",
    "DailyCheckForPrimaryNetwork",
    "DailyCheckReservationExpirations",
    "DailyMachineChecks",
    "DeactivateSerialOverLan",
    "MachineCheck",
    "NetboxCleanupComparisionResults",
    "NetboxCompareEnclosure",
    "NetboxCompareFullMachine",
    "NetboxCompareRemotePowerDevice",
    "NetboxCompareRemotePowerDevice",
    "NetboxFetchBMC",
    "NetboxFetchEnclosure",
    "NetboxFetchFullEnclosure",
    "NetboxFetchRemotePowerDevice",
    "NetboxFetchFullMachine",
    "NetboxFetchMachine",
    "NetboxFetchNetworkInterface",
    "RegenerateCobbler",
    "RegenerateMOTD",
    "RegenerateSerialConsole",
    "SendReservationInformation",
    "SendRestoredPassword",
    "SetupMachine",
    "SyncCobblerDHCP",
    "UpdateCobblerMachine",
    "UpdateCobblerRemotePowerDevice",
]
