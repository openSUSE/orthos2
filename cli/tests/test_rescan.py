"""
Tests that are verifying that all functionality that is related to the "rescan" command is working.
"""

import unittest

from . import OrthosCliTestCase


class RescanTests(OrthosCliTestCase):
    @unittest.skip("Too much setup at the moment")
    def test_rescan_status(self):
        # Arrange
        self.start_cli()

        # Act
        self.process.sendline("rescan <fqdn> status")

        # Cleanup
        self.stop_cli()

        # Assert
        self.assertTrue(False)

    @unittest.skip("Too much setup at the moment")
    def test_rescan_all(self):
        # Arrange
        self.start_cli()

        # Act
        self.process.sendline("rescan <fqdn> all")

        # Cleanup
        self.stop_cli()

        # Assert
        self.assertTrue(False)

    @unittest.skip("Too much setup at the moment")
    def test_rescan_misc(self):
        # Arrange
        self.start_cli()

        # Act
        self.process.sendline("rescan <fqdn> misc")

        # Cleanup
        self.stop_cli()

        # Assert
        self.assertTrue(False)

    @unittest.skip("Too much setup at the moment")
    def test_rescan_installations(self):
        # Arrange
        self.start_cli()

        # Act
        self.process.sendline("rescan <fqdn> installations")

        # Cleanup
        self.stop_cli()

        # Assert
        self.assertTrue(False)

    @unittest.skip("Too much setup at the moment")
    def test_rescan_networkinterfaces(self):
        # Arrange
        self.start_cli()

        # Act
        self.process.sendline("rescan <fqdn> networkinterfaces")

        # Cleanup
        self.stop_cli()

        # Assert
        self.assertTrue(False)


if __name__ == "__main__":
    unittest.main()
