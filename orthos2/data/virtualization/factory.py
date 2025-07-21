"""
Module to provide a method to create a concrete virtualization object.
"""

from typing import TYPE_CHECKING, Optional

from orthos2.data.virtualization import VirtualizationAPI
from orthos2.data.virtualization.libvirt import Libvirt

if TYPE_CHECKING:
    from orthos2.data.models.machine import Machine


def virtualization_api_factory(
    virt_api: Optional[int], machine: "Machine"
) -> Optional[VirtualizationAPI]:
    """
    Factory to create a concrete instance of one of the available virtualization API providers.
    """
    if virt_api == VirtualizationAPI.Type.LIBVIRT:
        return Libvirt(machine)
    return None
