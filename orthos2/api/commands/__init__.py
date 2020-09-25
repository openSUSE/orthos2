from api.commands.add import (AddAnnotationCommand, AddCommand, AddMachineCommand,
                              AddRemotePowerCommand, AddSerialConsoleCommand, AddVMCommand)
from api.commands.base import BaseAPIView, get_machine
from api.commands.delete import (DeleteCommand, DeleteMachineCommand, DeleteRemotePowerCommand,
                                 DeleteSerialConsoleCommand)
from api.commands.info import InfoCommand
from api.commands.power import PowerCommand
from api.commands.query import QueryCommand
from api.commands.regenerate import RegenerateCommand
from api.commands.release import ReleaseCommand
from api.commands.rescan import RescanCommand
from api.commands.reservationhistory import ReservationHistoryCommand
from api.commands.reserve import ReserveCommand
from api.commands.serverconfig import ServerConfigCommand
from api.commands.setup import SetupCommand

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
]
