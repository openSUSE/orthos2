"""
This module contains custom type shorthands that are required regularly in the codebase. The module should only be
imported with the "TYPE_CHECKING" guard to prevent import issues.
"""

from datetime import date, datetime
from typing import Optional, Union
from uuid import UUID

from django.contrib.auth.models import User
from django.db import models
from django.db.models.expressions import Combinable
from django.http import HttpRequest

from orthos2.data.models.architecture import Architecture
from orthos2.data.models.bmc import BMC
from orthos2.data.models.devicetype import DeviceType
from orthos2.data.models.domain import Domain
from orthos2.data.models.enclosure import Enclosure
from orthos2.data.models.machine import Machine
from orthos2.data.models.manufacturer import Manufacturer
from orthos2.data.models.netboxorthoscomparision import NetboxOrthosComparisionRun
from orthos2.data.models.networkinterface import NetworkInterface
from orthos2.data.models.remotepowerdevice import RemotePowerDevice
from orthos2.data.models.remotepowertype import RemotePowerType
from orthos2.data.models.serialconsoletype import SerialConsoleType
from orthos2.data.models.system import System


class AuthenticatedHttpRequest(HttpRequest):
    user: User  # type: ignore


MandatoryDateTimeField = models.DateTimeField[datetime, datetime]
OptionalDateTimeField = models.DateTimeField[Optional[datetime], Optional[datetime]]
MandatoryDateField = models.DateField[date, date]
OptionalDateField = models.DateField[Union[Combinable, date, None], Optional[date]]
MandatoryCharField = models.CharField[str, str]
MandatoryMachineForeignKey = models.ForeignKey[Union[Combinable, Machine], Machine]
OptionalMachineForeignKey = models.ForeignKey[
    Union[Combinable, Machine, None], Optional[Machine]
]
MandatoryUserForeignKey = models.ForeignKey[Union[Combinable, User], User]
OptionalUserForeignKey = models.ForeignKey[
    Union[Combinable, User, None], Optional[User]
]
MandatoryDeviceTypeForeignKey = models.ForeignKey[
    Union[Combinable, DeviceType], DeviceType
]
OptionalDeviceTypeForeignKey = models.ForeignKey[
    Union[Combinable, DeviceType, None], Optional[DeviceType]
]
MandatoryEnclosureForeignKey = models.ForeignKey[
    Union[Combinable, Enclosure], Enclosure
]
OptionalEnclosureForeignKey = models.ForeignKey[
    Union[Combinable, Enclosure, None], Optional[Enclosure]
]
MandatoryArchitectureForeignKey = models.ForeignKey[
    Union[Combinable, Architecture], Architecture
]
OptionalManufacturerForeignKey = models.ForeignKey[
    Union[Combinable, Manufacturer, None], Optional[Manufacturer]
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
OptionalRemotePowerTypeForeignKey = models.ForeignKey[
    Union[Combinable, "RemotePowerType", None], Optional["RemotePowerType"]
]
MandatoryRemotePowerTypeForeignKey = models.ForeignKey[
    Union[Combinable, RemotePowerType], RemotePowerType
]
MandatoryUUIDField = models.UUIDField[Union[str, UUID], UUID]
OptionalBMCForeignKey = models.ForeignKey[Union[Combinable, BMC, None], Optional[BMC]]
OptionalNetworkInterfaceForeignKey = models.ForeignKey[
    Union[Combinable, NetworkInterface, None], Optional[NetworkInterface]
]
MandatoryNetboxOrthosComparisionRunForeignKey = models.ForeignKey[
    Union[Combinable, NetboxOrthosComparisionRun], NetboxOrthosComparisionRun
]
