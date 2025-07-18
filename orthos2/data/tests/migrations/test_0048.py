from django.test import TestCase, override_settings
from django_test_migrations.migrator import Migrator

FAKE_POWER_TYPES = [
    {
        "fence": "redfish",
        "device": "bmc",
        "username": "root",
        "identity_file": "/root/.ssh/master",
        "use_hostname_as_port": True,
        "arch": ["x86_64", "aarch64"],
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
