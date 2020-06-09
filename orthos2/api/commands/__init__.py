from api.commands.base import BaseAPIView, get_machine
from api.commands.info import InfoCommand
from api.commands.query import QueryCommand
from api.commands.reserve import ReserveCommand
from api.commands.release import ReleaseCommand
from api.commands.reservationhistory import ReservationHistoryCommand
from api.commands.rescan import RescanCommand
from api.commands.regenerate import RegenerateCommand
from api.commands.serverconfig import ServerConfigCommand
from api.commands.setup import SetupCommand
from api.commands.power import PowerCommand
from api.commands.add import (AddCommand, AddVMCommand, AddMachineCommand, AddSerialConsoleCommand,
                              AddAnnotationCommand, AddRemotePowerCommand)
from api.commands.delete import (DeleteCommand, DeleteMachineCommand, DeleteSerialConsoleCommand,
                                 DeleteRemotePowerCommand)


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
