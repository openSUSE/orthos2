from django.core.management import CommandError
from django.test import TestCase
from django_test_migrations.migrator import Migrator


class TestDirectMigration0052(TestCase):
    """
    This test case checks the migration from 0051 to 0052.
    """

    def test_migration_0052(self):
        """
        Test the migration from 0051 to 0052, specifically testing that
        architecture and domain fields are correctly populated for RemotePowerDevice.
        """
        # Arrange
        migrator = Migrator(database="default")
        old_state = migrator.apply_initial_migration(
            ("data", "0051_alter_enclosure_description_and_more")
        )

        RemotePowerDevice = old_state.apps.get_model("data", "RemotePowerDevice")
        RemotePowerType = old_state.apps.get_model("data", "RemotePowerType")
        Domain = old_state.apps.get_model("data", "Domain")

        # Create an existing domain
        Domain.objects.create(
            name="example.com",
            ip_v4="192.168.1.0",
            ip_v6="2001:db8::",
            dynamic_range_v4_start="192.168.1.200",
            dynamic_range_v4_end="192.168.1.250",
            dynamic_range_v6_start="2001:db8::200",
            dynamic_range_v6_end="2001:db8::250",
        )

        # RemotePowerDevice needs a fence agent
        fence_agent = RemotePowerType.objects.create(
            name="apc_test", device="rpowerdevice"
        )

        # Create RemotePowerDevice
        rpd1 = RemotePowerDevice.objects.create(
            fqdn="pdu.example.com",
            mac="AA:BB:CC:DD:EE:01",
            fence_agent=fence_agent,
        )

        # Act
        new_state = migrator.apply_tested_migration(
            ("data", "0052_remotepowerdevice_architecture_and_more")
        )

        # Assert
        RemotePowerDeviceNew = new_state.apps.get_model("data", "RemotePowerDevice")

        rpd1_new = RemotePowerDeviceNew.objects.get(id=rpd1.id)
        self.assertEqual(rpd1_new.domain.name, "example.com")
        self.assertEqual(rpd1_new.architecture.name, "embedded")

        # Cleanup
        migrator.reset()

    def test_migration_0052_missing_domain(self):
        """
        Test that migration 0052 fails with CommandError if the domain
        required by a RemotePowerDevice does not exist.
        """
        # Arrange
        migrator = Migrator(database="default")
        old_state = migrator.apply_initial_migration(
            ("data", "0051_alter_enclosure_description_and_more")
        )

        RemotePowerDevice = old_state.apps.get_model("data", "RemotePowerDevice")
        RemotePowerType = old_state.apps.get_model("data", "RemotePowerType")

        # RemotePowerDevice needs a fence agent
        fence_agent = RemotePowerType.objects.create(
            name="apc_test", device="rpowerdevice"
        )

        # Create RemotePowerDevice with a domain that does not exist in the database
        test_rpd = RemotePowerDevice.objects.create(
            fqdn="pdu.missing-domain.com",
            mac="AA:BB:CC:DD:EE:02",
            fence_agent=fence_agent,
        )

        # Act & Assert
        with self.assertRaisesMessage(
            CommandError,
            'Domain "missing-domain.com" does not exist! Please create it first.',
        ):
            migrator.apply_tested_migration(
                ("data", "0052_remotepowerdevice_architecture_and_more")
            )

        # Cleanup - Delete offending object
        test_rpd.delete()
        migrator.reset()

    def test_migration_0052_missing_architecture(self):
        """
        Test that migration 0052 fails with CommandError if the "embedded"
        architecture does not exist.
        """
        # Arrange
        migrator = Migrator(database="default")
        old_state = migrator.apply_initial_migration(
            ("data", "0051_alter_enclosure_description_and_more")
        )

        Architecture = old_state.apps.get_model("data", "Architecture")

        # Make sure "embedded" architecture does not exist
        Architecture.objects.filter(name="embedded").delete()

        # Act & Assert
        with self.assertRaisesMessage(
            CommandError,
            '"embedded" architecture does not exist! Please create it first.',
        ):
            migrator.apply_tested_migration(
                ("data", "0052_remotepowerdevice_architecture_and_more")
            )

        # Cleanup - Recreate missing object
        Architecture.objects.create(name="embedded")
        migrator.reset()
