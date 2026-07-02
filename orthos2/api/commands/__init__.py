from orthos2.api.commands.add import (
    AddAnnotationCommandGet,
    AddAnnotationCommandPost,
    AddBMCCommandGet,
    AddBMCCommandPost,
    AddCommand,
    AddMachineCommand,
    AddRemotePowerCommandGet,
    AddRemotePowerCommandPost,
    AddRemotePowerDeviceCommand,
    AddSerialConsoleCommandGet,
    AddSerialConsoleCommandPost,
    AddVMCommandGet,
    AddVMCommandPost,
)
from orthos2.api.commands.delete import (
    DeleteCommand,
    DeleteMachineCommand,
    DeleteRemotePowerCommand,
    DeleteRemotePowerDeviceCommand,
    DeleteSerialConsoleCommand,
)
from orthos2.api.commands.info import (
    EnclosureInfoCommand,
    InfoCommand,
    RemotePowerDeviceInfoCommand,
)
from orthos2.api.commands.power import PowerCommand
from orthos2.api.commands.query import QueryCommand
from orthos2.api.commands.regenerate import RegenerateCommand
from orthos2.api.commands.release import ReleaseCommand
from orthos2.api.commands.rescan import RescanCommand
from orthos2.api.commands.reservationhistory import ReservationHistoryCommand
from orthos2.api.commands.reserve import ReserveCommandGet, ReserveCommandPost
from orthos2.api.commands.serverconfig import ServerConfigCommand
from orthos2.api.commands.setup import SetupCommand

__all__ = [
    "EnclosureInfoCommand",
    "RemotePowerDeviceInfoCommand",
    "InfoCommand",
    "QueryCommand",
    "ReserveCommandGet",
    "ReserveCommandPost",
    "ReleaseCommand",
    "ReservationHistoryCommand",
    "RescanCommand",
    "RegenerateCommand",
    "ServerConfigCommand",
    "SetupCommand",
    "PowerCommand",
    "AddCommand",
    "AddVMCommandGet",
    "AddVMCommandPost",
    "AddMachineCommand",
    "AddSerialConsoleCommandGet",
    "AddSerialConsoleCommandPost",
    "AddAnnotationCommandGet",
    "AddAnnotationCommandPost",
    "AddRemotePowerCommandPost",
    "AddRemotePowerCommandGet",
    "DeleteCommand",
    "DeleteMachineCommand",
    "DeleteSerialConsoleCommand",
    "DeleteRemotePowerCommand",
    "DeleteRemotePowerDeviceCommand",
    "AddBMCCommandPost",
    "AddBMCCommandGet",
    "AddRemotePowerDeviceCommand",
]
