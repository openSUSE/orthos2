from orthos2.api.commands.add import (
    AddAnnotationCommandGet,
    AddAnnotationCommandPost,
    AddBMCCommandGet,
    AddBMCCommandPost,
    AddCommand,
    AddDeviceTypeCommand,
    AddMachineCommand,
    AddManufacturerCommand,
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
    DeleteDeviceTypeCommand,
    DeleteMachineCommand,
    DeleteManufacturerCommand,
    DeleteNetworkInterfaceCommand,
    DeleteRemotePowerCommand,
    DeleteRemotePowerDeviceCommand,
    DeleteSerialConsoleCommand,
)
from orthos2.api.commands.edit import (
    EditCommand,
    EditDeviceTypeCommand,
    EditManufacturerCommand,
)
from orthos2.api.commands.info import (
    DeviceTypeInfoCommand,
    EnclosureInfoCommand,
    InfoCommand,
    ManufacturerInfoCommand,
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
    "ManufacturerInfoCommand",
    "DeviceTypeInfoCommand",
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
    "DeleteNetworkInterfaceCommand",
    "AddBMCCommandPost",
    "AddBMCCommandGet",
    "AddRemotePowerDeviceCommand",
    "AddManufacturerCommand",
    "DeleteManufacturerCommand",
    "EditCommand",
    "EditManufacturerCommand",
    "AddDeviceTypeCommand",
    "DeleteDeviceTypeCommand",
    "EditDeviceTypeCommand",
]
