"""
Tests that are verifying that all functionality that is related to the "exit" command is working.
"""

import unittest

from . import OrthosCliTestCase


class InfoTests(OrthosCliTestCase):
    @unittest.skip("Too much setup at the moment")
    def test_info(self) -> None:
        # Arrange
        self.start_cli(username="admin")

        # Act
        if self.process is None:
            self.fail("CLI process not successfully spawned!")
        self.process.sendline("info <fqdn>")

        # Cleanup
        self.stop_cli()

        # Assert
        self.assertTrue(False)


if __name__ == "__main__":
    unittest.main()
