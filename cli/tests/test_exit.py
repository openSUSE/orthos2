"""
Tests that are verifying that all functionality that is related to the "exit" command is working.
"""

import unittest

from . import OrthosCliTestCase


class ExitTests(OrthosCliTestCase):
    def test_exit(self):
        """
        Test to verify that the CLI can be exited.
        """
        # Arrange
        self.start_cli()

        # Act
        self.process.sendline("quit")

        # Assert
        self.process.expect("Good bye, have a lot of fun...")
        self.process.wait()
        self.assertEqual(self.process.exitstatus, 0)


if __name__ == "__main__":
    unittest.main()
