"""
Tests that are verifying that all functionality that is related to the "reserve" command is working.
"""

import unittest

from . import OrthosCliTestCase


class ReserveTests(OrthosCliTestCase):
    @unittest.skip("Too much setup at the moment")
    def test_reserve(self):
        # Arrange
        self.start_cli()

        # Act
        self.process.sendline("reserve <fqdn>")

        # Cleanup
        self.stop_cli()

        # Assert
        self.assertTrue(False)


if __name__ == "__main__":
    unittest.main()
