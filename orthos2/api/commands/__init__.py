from orthos2.api.commands.add import (AddAnnotationCommand, AddBMCCommand,
                                      AddCommand, AddMachineCommand,
                                      AddRemotePowerCommand,
                                      AddRemotePowerDeviceCommand,
                                      AddSerialConsoleCommand, AddVMCommand)
from orthos2.api.commands.delete import (DeleteCommand, DeleteMachineCommand,
                                         DeleteRemotePowerCommand,
                                         DeleteRemotePowerDeviceCommand,
                                         DeleteSerialConsoleCommand)
from orthos2.api.commands.info import InfoCommand
from orthos2.api.commands.power import PowerCommand
from orthos2.api.commands.query import QueryCommand
from orthos2.api.commands.regenerate import RegenerateCommand
from orthos2.api.commands.release import ReleaseCommand
from orthos2.api.commands.rescan import RescanCommand
from orthos2.api.commands.reservationhistory import ReservationHistoryCommand
from orthos2.api.commands.reserve import ReserveCommand
from orthos2.api.commands.serverconfig import ServerConfigCommand
from orthos2.api.commands.setup import SetupCommand

__all__ = [
    'InfoCommand',
    'QueryCommand',
    'ReserveCommand',
    'ReleaseCommand',
    'ReservationHistoryCommand',
    'RescanCommand',
    'RegenerateCommand',
    'ServerConfigCommand',
    'SetupCommand',
    'PowerCommand',
    'AddCommand',
    'AddVMCommand',
    'AddMachineCommand',
    'AddSerialConsoleCommand',
    'AddAnnotationCommand',
    'AddRemotePowerCommand',
    'DeleteCommand',
    'DeleteMachineCommand',
    'DeleteSerialConsoleCommand',
    'DeleteRemotePowerCommand',
    'DeleteRemotePowerDeviceCommand',
    'AddBMCCommand',
    'AddRemotePowerDeviceCommand'
]
