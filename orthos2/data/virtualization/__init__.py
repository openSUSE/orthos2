"""
Module to define the common and abstract components to implement a concrete virtualization provider.
"""

import logging
from abc import abstractmethod
from typing import TYPE_CHECKING, Any, List, Tuple

from orthos2.data.models.remotepowertype import RemotePowerType

if TYPE_CHECKING:
    from orthos2.data.models.machine import Machine

logger = logging.getLogger("models")


class VirtualizationAPI:
    """
    Abstract base class that virtualization API providers have to implement.
    """

    class Type:
        """
        Embedded class to have a Django compatible way of offering the available virtualization APIs.
        """

        LIBVIRT = 0

        @classmethod
        def to_str(cls, index: int) -> str:
            """Return type as string (Virtualization API type name) by index."""
            for type_tuple in VirtualizationAPI.TYPE_CHOICES:
                if int(index) == type_tuple[0]:
                    return type_tuple[1]
            raise Exception(
                "Virtualization API type with ID '{}' doesn't exist!".format(index)
            )

        @classmethod
        def to_int(cls, name: str) -> int:
            """Return type as integer if name matches."""
            for type_tuple in VirtualizationAPI.TYPE_CHOICES:
                if name.lower() == type_tuple[1].lower():
                    return type_tuple[0]
            raise Exception("Virtualization API type '{}' not found!".format(name))

    TYPE_CHOICES = ((Type.LIBVIRT, "libvirt"),)

    def __init__(self, type: int, host: "Machine") -> None:
        """
        Constructor for the parent class of virtualization APIs.
        """
        self.type = type
        self.host = host

    def get_image_list(self) -> Tuple[List[str], List[Tuple[str, str]]]:
        raise NotImplementedError

    @abstractmethod
    def _create(self, vm: "Machine", *args: Any, **kwargs: Any) -> bool:
        """
        Wrapper function for creating a VM. This should implement the provider specific real creation of a VM.
        """

    def create(self, *args: Any, **kwargs: Any) -> "Machine":
        """
        Create a virtual machine.

        Method returns a new `Machine` object and calls the subclass to actually create the virtual
        machine physically.
        """
        from django.contrib.auth.models import User

        from orthos2.data.models import (
            Architecture,
            Machine,
            RemotePower,
            SerialConsole,
            SerialConsoleType,
            System,
        )

        vm = Machine()
        vm.unsaved_networkinterfaces = []

        vm.architecture = Architecture.objects.get(name=kwargs["architecture"])
        vm.system = System.objects.get(pk=kwargs["system"])

        self._create(vm, *args, **kwargs)

        vm.check_connectivity = Machine.Connectivity.ALL
        vm.collect_system_information = True
        vm.save()

        for networkinterface in vm.unsaved_networkinterfaces[1:]:
            networkinterface.machine = vm
            networkinterface.save()
        try:
            fence_agent = RemotePowerType.objects.get(name="virsh")
            vm.remotepower = RemotePower(fence_agent=fence_agent)
        except RemotePowerType.DoesNotExist:
            logger.warning(
                "RemotePowerType 'virsh' not found. Please add remotepower for VM %s manually!",
                vm.hostname,
            )
        vm.remotepower.save()

        if self.host.has_serialconsole():
            stype = SerialConsoleType.objects.get(name="libvirt/qemu")
            if not stype:
                raise Exception("Bug: SerialConsoleType not found")
            vm.serialconsole = SerialConsole(stype=stype, baud_rate=115200)
            vm.serialconsole.save()

        if vm.vnc["enabled"]:
            vm.annotations.create(
                text=f"VNC enabled: {self.host.fqdn}:{vm.vnc['port']}",
                reporter=User.objects.get(username="admin"),
            )

        return vm

    @abstractmethod
    def _remove(self, *args: Any, **kwargs: Any) -> bool:
        """
        Wrapper function for removing a VM. This should implement the provider specific real creation of a VM.
        """

    def remove(self, *args: Any, **kwargs: Any) -> bool:
        return self._remove(*args, **kwargs)

    def get_list(self) -> str:
        raise NotImplementedError

    def __str__(self) -> str:
        return self.Type.to_str(self.type)

    def __repr__(self) -> str:
        return "<VirtualizationAPI: {} ({})>".format(self, self.host.fqdn)
