"""
This module contains custom type shorthands that are required regularly in the codebase. The module should only be
imported with the "TYPE_CHECKING" guard to prevent import issues.
"""

from datetime import date, datetime
from typing import Optional, Union

from django.contrib.auth.models import User
from django.db import models
from django.db.models.expressions import Combinable
from django.http import HttpRequest

from orthos2.data.models.architecture import Architecture
from orthos2.data.models.domain import Domain
from orthos2.data.models.enclosure import Enclosure
from orthos2.data.models.machine import Machine
from orthos2.data.models.machinegroup import MachineGroup
from orthos2.data.models.platform import Platform
from orthos2.data.models.remotepowerdevice import RemotePowerDevice
from orthos2.data.models.serialconsoletype import SerialConsoleType
from orthos2.data.models.system import System


class AuthenticatedHttpRequest(HttpRequest):
    user: User  # type: ignore


MandatoryDateTimeField = models.DateTimeField[datetime, datetime]
OptionalDateTimeField = models.DateTimeField[Optional[datetime], Optional[datetime]]
MandatoryDateField = models.DateField[date, date]
OptionalDateField = models.DateField[Union[Combinable, date, None], Optional[date]]
MandatoryMachineForeignKey = models.ForeignKey[Union[Combinable, Machine], Machine]
OptionalMachineForeignKey = models.ForeignKey[
    Union[Combinable, Machine, None], Optional[Machine]
]
MandatoryUserForeignKey = models.ForeignKey[Union[Combinable, User], User]
OptionalUserForeignKey = models.ForeignKey[
    Union[Combinable, User, None], Optional[User]
]
MandatoryMachineGroupForeignKey = models.ForeignKey[
    Union[Combinable, MachineGroup], MachineGroup
]
OptionalMachineGroupForeignKey = models.ForeignKey[
    Union[Combinable, MachineGroup, None], Optional[MachineGroup]
]
MandatoryPlatformForeignKey = models.ForeignKey[Union[Combinable, Platform], Platform]
OptionalPlatformForeignKey = models.ForeignKey[
    Union[Combinable, Platform, None], Optional[Platform]
]
MandatoryEnclosureForeignKey = models.ForeignKey[
    Union[Combinable, Enclosure], Enclosure
]
MandatoryArchitectureForeignKey = models.ForeignKey[
    Union[Combinable, Architecture], Architecture
]
MandatoryMachineOneToOneField = models.OneToOneField[
    Union[Combinable, Machine], Machine
]
MandatoryDomainForeignKey = models.ForeignKey[Union[Combinable, Domain], Domain]
MandatorySystemForeignKey = models.ForeignKey[Union[Combinable, System], System]
MandatorySerialConsoleTypeForeignKey = models.ForeignKey[
    Union[Combinable, SerialConsoleType], SerialConsoleType
]
OptionalSmallIntegerField = models.SmallIntegerField[
    Union[Combinable, str, float, int, None], Optional[int]
]
OptionalRemotePowerDeviceForeignKey = models.ForeignKey[
    Union[Combinable, RemotePowerDevice, None], Optional[RemotePowerDevice]
]
