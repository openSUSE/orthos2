"""
Tests that are verifying that all functionality that is related to the "power" command is working.
"""

import unittest

from . import OrthosCliTestCase


class PowerTests(OrthosCliTestCase):
    @unittest.skip("Too much setup at the moment")
    def test_power_on(self) -> None:
        # Arrange
        self.start_cli(username="admin")

        # Act
        if self.process is None:
            self.fail("CLI process not successfully spawned!")
        self.process.sendline("power <fqdn> on")

        # Cleanup
        self.stop_cli()

        # Assert
        self.assertTrue(False)

    @unittest.skip("Too much setup at the moment")
    def test_power_off(self) -> None:
        # Arrange
        self.start_cli(username="admin")

        # Act
        if self.process is None:
            self.fail("CLI process not successfully spawned!")
        self.process.sendline("power <fqdn> off")

        # Cleanup
        self.stop_cli()

        # Assert
        self.assertTrue(False)

    @unittest.skip("Too much setup at the moment")
    def test_power_off_ssh(self) -> None:
        # Arrange
        self.start_cli(username="admin")

        # Act
        if self.process is None:
            self.fail("CLI process not successfully spawned!")
        self.process.sendline("power <fqdn> off-ssh")

        # Cleanup
        self.stop_cli()

        # Assert
        self.assertTrue(False)

    @unittest.skip("Too much setup at the moment")
    def test_power_off_remotepower(self) -> None:
        # Arrange
        self.start_cli(username="admin")

        # Act
        if self.process is None:
            self.fail("CLI process not successfully spawned!")
        self.process.sendline("power <fqdn> off-remotepower")

        # Cleanup
        self.stop_cli()

        # Assert
        self.assertTrue(False)

    @unittest.skip("Too much setup at the moment")
    def test_power_reboot(self) -> None:
        # Arrange
        self.start_cli(username="admin")

        # Act
        if self.process is None:
            self.fail("CLI process not successfully spawned!")
        self.process.sendline("power <fqdn> reboot")

        # Cleanup
        self.stop_cli()

        # Assert
        self.assertTrue(False)

    @unittest.skip("Too much setup at the moment")
    def test_power_reboot_ssh(self) -> None:
        # Arrange
        self.start_cli(username="admin")

        # Act
        if self.process is None:
            self.fail("CLI process not successfully spawned!")
        self.process.sendline("power <fqdn> reboot-ssh")

        # Cleanup
        self.stop_cli()

        # Assert
        self.assertTrue(False)

    @unittest.skip("Too much setup at the moment")
    def test_power_reboot_remotepower(self) -> None:
        # Arrange
        self.start_cli(username="admin")

        # Act
        if self.process is None:
            self.fail("CLI process not successfully spawned!")
        self.process.sendline("power <fqdn> reboot-remotepower")

        # Cleanup
        self.stop_cli()

        # Assert
        self.assertTrue(False)

    @unittest.skip("Too much setup at the moment")
    def test_power_status(self) -> None:
        # Arrange
        self.start_cli(username="admin")

        # Act
        if self.process is None:
            self.fail("CLI process not successfully spawned!")
        self.process.sendline("power <fqdn> status")

        # Cleanup
        self.stop_cli()

        # Assert
        self.assertTrue(False)


if __name__ == "__main__":
    unittest.main()
