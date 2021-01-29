from orthos2.api.commands.base import BaseAPIView, get_machine
from orthos2.api.commands.info import InfoCommand
from orthos2.api.commands.query import QueryCommand
from orthos2.api.commands.reserve import ReserveCommand
from orthos2.api.commands.release import ReleaseCommand
from orthos2.api.commands.reservationhistory import ReservationHistoryCommand
from orthos2.api.commands.rescan import RescanCommand
from orthos2.api.commands.regenerate import RegenerateCommand
from orthos2.api.commands.serverconfig import ServerConfigCommand
from orthos2.api.commands.setup import SetupCommand
from orthos2.api.commands.power import PowerCommand
from orthos2.api.commands.add import (AddCommand, AddVMCommand, AddMachineCommand,
                                      AddSerialConsoleCommand, AddAnnotationCommand,
                                      AddRemotePowerCommand, AddBMCCommand)
from orthos2.api.commands.delete import (DeleteCommand, DeleteMachineCommand,
                                         DeleteSerialConsoleCommand, DeleteRemotePowerCommand)


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
    'AddBMCCommand',
]
