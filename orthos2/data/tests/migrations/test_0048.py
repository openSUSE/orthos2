from django.test import TestCase, override_settings
from django_test_migrations.migrator import Migrator

FAKE_POWER_TYPES = [
    {
        "fence": "virsh",
        "device": "hypervisor",
        "username": "root",
        "identity_file": "/root/.ssh/master",
        "arch": ["x86_64", "aarch64"],
        "use_hostname_as_port": True,
        "system": ["KVM VM"],
    },
    {
        "fence": "ipmilanplus",
        "device": "bmc",
        "username": "xxx",
        "password": "XXX",
        "arch": ["x86_64", "aarch64"],
        "system": ["Bare Metal"],
    },
    {
        "fence": "apc",
        "device": "rpower_device",
        "username": "xxx",
        "password": "XXX",
        "port": True,
        "system": ["Bare Metal"],
    },
]


class TestDirectMigration0048(TestCase):
    """
    This test case checks the migration from 0047 to 0048.
    """

    @override_settings(REMOTEPOWER_TYPES=FAKE_POWER_TYPES)
    def test_migration_0048(self):
        """
        Test the migration from 0047 to 0048.
        """
        # Arrange
        migrator = Migrator(database="default")
        old_state = migrator.apply_initial_migration(("data", "0047_machine_netbox_id"))
        System = old_state.apps.get_model("data", "System")
        System.objects.create(name="Bare Metal")
        System.objects.create(name="KVM VM")

        # Act
        new_state = migrator.apply_tested_migration(
            ("data", "0048_reintroduce_remotepowertype"),
        )
        RemotePowerType = new_state.apps.get_model("data", "RemotePowerType")

        # Assert
        # 3 Dummy + 3 from settings
        assert RemotePowerType.objects.count() == 6
        apc_fence = RemotePowerType.objects.get(name="apc")
        assert apc_fence.architectures.count() == 0
        assert apc_fence.systems.count() == 1
        assert apc_fence.device == "rpower_device"
        assert apc_fence.username == "xxx"
        assert apc_fence.password == "XXX"
        assert apc_fence.use_port is True

        # Cleanup:
        migrator.reset()

    @override_settings(REMOTEPOWER_TYPES=FAKE_POWER_TYPES)
    def test_migration_0048_set_fence_agents(self):
        # Arrange
        migrator = Migrator(database="default")
        old_state = migrator.apply_initial_migration(("data", "0047_machine_netbox_id"))
        # Get models from Django
        Enclosure = old_state.apps.get_model("data", "Enclosure")
        System = old_state.apps.get_model("data", "System")
        ServerConfig = old_state.apps.get_model("data", "ServerConfig")
        Domain = old_state.apps.get_model("data", "Domain")
        Architecture = old_state.apps.get_model("data", "Architecture")
        MachineOld = old_state.apps.get_model("data", "Machine")
        BMC = old_state.apps.get_model("data", "BMC")
        RemotePower = old_state.apps.get_model("data", "RemotePower")
        RemotePowerDevice = old_state.apps.get_model("data", "RemotePowerDevice")
        # Systems to allow migration of RemotePowerTypes
        system_bare_metal = System.objects.create(name="Bare Metal")
        system_kvm_vm = System.objects.create(name="KVM VM")
        # ServerConfig "domain.validendings"
        ServerConfig(key="domain.validendings", value="orthos2.test").save()
        # Domain
        domain_test = Domain.objects.create(
            name="orthos2.test",
            ip_v4="192.0.2.0",
            ip_v6="2001:db8::0",
            dynamic_range_v4_start="192.0.2.200",
            dynamic_range_v4_end="192.0.2.250",
            dynamic_range_v6_start="2001:db8::200",
            dynamic_range_v6_end="2001:db8::250",
        )
        # Get architectures for machines
        test_architecture = Architecture.objects.get(name="x86_64")
        # Machine with BMC --> Act as Hypervisor for third machine
        enclosure_old_hypervisor = Enclosure.objects.create(name="hypervisor")
        enclosure_old_hypervisor.save()
        machine_old_hypervisor = MachineOld.objects.create(
            fqdn="hypervisor.orthos2.test",
            architecture=test_architecture,
            enclosure=enclosure_old_hypervisor,
            system=system_bare_metal,
            fqdn_domain=domain_test,
            vm_dedicated_host=True,
            virt_api_int=0,
        )
        BMC.objects.create(
            fqdn="hypervisor-sp.orthos2.test",
            mac="AA:BB:CC:DD:EE:FF",
            fence_name="ipmilanplus",
            machine=machine_old_hypervisor,
        )
        RemotePower.objects.create(machine=machine_old_hypervisor)
        # Machine with RemotePowerDevice
        enclosure_old_rpower = Enclosure.objects.create(name="machine-rpower")
        machine_old_rpower_device = MachineOld.objects.create(
            fqdn="machine-rpower.orthos2.test",
            architecture=test_architecture,
            enclosure=enclosure_old_rpower,
            system=system_bare_metal,
            fqdn_domain=domain_test,
        )
        rpower_device = RemotePowerDevice.objects.create(
            fqdn="rpower.orthos2.test",
            mac="AA:BB:CC:DD:EE:EF",
            username="test",
            password="test",
            fence_name="apc",
        )
        RemotePower.objects.create(
            machine=machine_old_rpower_device,
            remote_power_device=rpower_device,
        )
        # Machine with Hypervisor
        enclosure_old_kvm_vm = Enclosure.objects.create(name="kvm-vm")
        machine_old_kvm_vm = MachineOld.objects.create(
            fqdn="kvm-vm.orthos2.test",
            architecture=test_architecture,
            enclosure=enclosure_old_kvm_vm,
            system=system_kvm_vm,
            fqdn_domain=domain_test,
            hypervisor=machine_old_hypervisor,
        )
        RemotePower.objects.create(
            machine=machine_old_kvm_vm,
            fence_name="virsh",
        )

        # Act
        new_state = migrator.apply_tested_migration(
            ("data", "0048_reintroduce_remotepowertype"),
        )

        # Assert
        RemotePowerNew = new_state.apps.get_model("data", "RemotePower")
        BMCNew = new_state.apps.get_model("data", "BMC")
        RemotePowerDeviceNew = new_state.apps.get_model("data", "RemotePowerDevice")

        # Assert that no fence_agent field has set the dummy remote power type
        rpower_device_query_set = RemotePowerDeviceNew.objects.filter(
            fence_agent__name__contains="Dummy"
        )
        self.assertEqual(
            rpower_device_query_set.count(),
            0,
            msg="There was an rpower objects that had a dummy fence agent",
        )
        bmc_query_set = BMCNew.objects.filter(fence_agent__name__contains="Dummy")
        self.assertEqual(
            bmc_query_set.count(),
            0,
            msg="There was an rpower objects that had a dummy fence agent",
        )
        rpower_query_set = RemotePowerNew.objects.filter(
            fence_agent__name__contains="Dummy"
        )
        self.assertEqual(
            rpower_query_set.count(),
            0,
            msg="There was an rpower objects that had a dummy fence agent",
        )
