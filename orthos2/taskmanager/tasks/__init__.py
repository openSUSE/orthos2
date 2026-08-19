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
    "NetboxCompareDeviceType",
    "NetboxCompareEnclosure",
    "NetboxCompareFullMachine",
    "NetboxCompareManufacturer",
    "NetboxCompareRemotePowerDevice",
    "NetboxCompareRemotePowerDevice",
    "NetboxFetchBMC",
    "NetboxFetchDeviceType",
    "NetboxFetchEnclosure",
    "NetboxFetchFullDeviceType",
    "NetboxFetchFullEnclosure",
    "NetboxFetchFullManufacturer",
    "NetboxFetchRemotePowerDevice",
    "NetboxFetchFullMachine",
    "NetboxFetchMachine",
    "NetboxFetchManufacturer",
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
