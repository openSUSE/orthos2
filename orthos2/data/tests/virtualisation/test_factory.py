from django.test import TestCase

from orthos2.data.virtualization import VirtualizationAPI
from orthos2.data.virtualization.factory import virtualization_api_factory
from orthos2.data.virtualization.libvirt import Libvirt


class VirtualizationFactoryTest(TestCase):
    def test_factory_none(self):
        """
        Test to verify that the factory returns None in case an unkown provider is requested.
        """
        self.assertIsNone(virtualization_api_factory(999, None))  # type: ignore

    def test_factory_libvirt(self):
        """
        Test to verify that the factory can produce a libvirt implementation of the virtualization API.
        """
        self.assertTrue(
            isinstance(
                virtualization_api_factory(VirtualizationAPI.Type.LIBVIRT, None),  # type: ignore
                Libvirt,
            )
        )
