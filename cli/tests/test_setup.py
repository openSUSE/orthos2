"""
Tests that are verifying that all functionality that is related to the "setup" command is working.
"""

import unittest

from . import OrthosCliTestCase


class SetupTests(OrthosCliTestCase):
    @unittest.skip("Too much setup at the moment")
    def test_list(self) -> None:
        # Arrange
        self.start_cli()

        # Act
        if self.process is None:
            self.fail("CLI process not successfully spawned!")
        self.process.sendline("setup <fqdn> list")

        # Cleanup
        self.stop_cli()

        # Assert
        self.assertTrue(False)

    @unittest.skip("Too much setup at the moment")
    def test_specific(self) -> None:
        # Arrange
        self.start_cli()

        # Act
        if self.process is None:
            self.fail("CLI process not successfully spawned!")
        self.process.sendline("setup <fqdn> <distro>")

        # Cleanup
        self.stop_cli()

        # Assert
        self.assertTrue(False)


if __name__ == "__main__":
    unittest.main()
