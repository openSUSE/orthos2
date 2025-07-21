from typing import Any
from unittest.mock import MagicMock

from django.test import TestCase

from orthos2.data.models.architecture import Architecture
from orthos2.data.models.domain import Domain
from orthos2.data.models.machine import Machine
from orthos2.data.models.remotepowertype import RemotePowerType
from orthos2.data.models.serverconfig import ServerConfig
from orthos2.data.models.system import System
from orthos2.data.virtualization import VirtualizationAPI


class VirtualizationAPITest(TestCase):
    def test_type_to_str(self):
        """
        Test that converting the type to str works as expected.
        """
        self.assertEqual(VirtualizationAPI.Type.to_str(0), "libvirt")

    def test_type_to_str_error(self):
        """
        Test that converting an invalid type to str raises an exception.
        """
        self.assertRaises(Exception, VirtualizationAPI.Type.to_str, 999)

    def test_type_to_int(self):
        """
        Test that converting the type to int works as expected.
        """
        self.assertEqual(VirtualizationAPI.Type.to_int("libvirt"), 0)

    def test_type_to_int_error(self):
        """
        Test that converting an invalid type to int raises an exception.
        """
        self.assertRaises(Exception, VirtualizationAPI.Type.to_int, "garbage")

    def test_get_image_list(self):
        """
        Test to verify that the base method raises the NotImplementedError.
        """
        # Arrange
        virt_api = VirtualizationAPI(1, None)  # type: ignore

        # Act & Assert
        self.assertRaises(NotImplementedError, virt_api.get_image_list)

    def test_create(self):
        """
        TODO
        """

        # Arrange
        def fake_create(vm: "Machine", *args: Any, **kwargs: Any):
            vm.fqdn = "mytest.orthos2.test"
            vm.hypervisor = fake_hypervisor
            vm.vnc = {"enabled": False, "port": 5901}
            return True

        system_kvm = System.objects.get(name="VM KVM")
        RemotePowerType.objects.create(name="virsh", device="hypervisor")
        ServerConfig.objects.create(key="domain.validendings", value="orthos2.test")
        Domain.objects.create(
            name="orthos2.test",
            ip_v4="127.0.0.1",
            ip_v6="::1",
            dynamic_range_v4_start="127.0.0.1",
            dynamic_range_v4_end="127.0.0.1",
            dynamic_range_v6_start="::1",
            dynamic_range_v6_end="::1",
        )
        fake_hypervisor = Machine.objects.create(
            fqdn="hypervisor.orthos2.test",
            vm_dedicated_host=True,
            virt_api_int=0,
            system=System.objects.get(name="BareMetal"),
            architecture=Architecture.objects.get(name="x86_64"),
        )
        virt_api = VirtualizationAPI(0, fake_hypervisor)
        virt_api._create = fake_create  # type: ignore

        # Act
        virt_api.create(architecture="x86_64", system=system_kvm.pk)

        # Assert
        self.assertTrue(True)

    def test_remove(self):
        """
        TODO
        """
        # Arrange
        virt_api = VirtualizationAPI(1, None)  # type: ignore
        virt_api._remove = MagicMock(return_value=True)  # type: ignore

        # Act
        result = virt_api.remove()

        # Assert
        self.assertTrue(result)

    def test_get_list(self):
        """
        Test to verify that the base method raises the NotImplementedError.
        """
        # Arrange
        virt_api = VirtualizationAPI(1, None)  # type: ignore

        # Act & Assert
        self.assertRaises(NotImplementedError, virt_api.get_list)

    def test_str(self):
        """
        Test to verify that the string representation of the object is stable.
        """
        # Arrange
        virt_api = VirtualizationAPI(0, None)  # type: ignore

        # Act & Assert
        self.assertEqual(str(virt_api), "libvirt")

    def test_repr(self):
        """
        Test to verify that the __repr__ of the object is working as desired.
        """
        # Arrange
        virt_api = VirtualizationAPI(0, None)  # type: ignore
        virt_api.host = MagicMock()
        virt_api.host.fqdn = "my.test.host"

        # Act & Assert
        self.assertEqual(repr(virt_api), "<VirtualizationAPI: libvirt (my.test.host)>")
