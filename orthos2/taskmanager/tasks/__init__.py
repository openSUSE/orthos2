from .cobbler import RegenerateCobbler, SyncCobblerDHCP, UpdateCobblerMachine
from .daily import (
    DailyCheckForPrimaryNetwork,
    DailyCheckReservationExpirations,
    DailyMachineChecks,
)
from .machinetasks import MachineCheck, RegenerateMOTD
from .netbox import (
    NetboxFetchBMC,
    NetboxFetchEnclosure,
    NetboxFetchFullMachine,
    NetboxFetchMachine,
    NetboxFetchNetworkInterface,
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

__all__ = [
    "RegenerateCobbler",
    "SyncCobblerDHCP",
    "UpdateCobblerMachine",
    "DailyCheckForPrimaryNetwork",
    "DailyCheckReservationExpirations",
    "DailyMachineChecks",
    "MachineCheck",
    "RegenerateMOTD",
    "NetboxFetchBMC",
    "NetboxFetchEnclosure",
    "NetboxFetchFullMachine",
    "NetboxFetchMachine",
    "NetboxFetchNetworkInterface",
    "CheckForPrimaryNetwork",
    "CheckMultipleAccounts",
    "CheckReservationExpiration",
    "SendReservationInformation",
    "SendRestoredPassword",
    "RegenerateSerialConsole",
    "SetupMachine",
]
