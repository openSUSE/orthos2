"""
Tests that are verifying that all functionality that is related to the "auth" command is working.
"""

import unittest

from . import OrthosCliTestCase


class AuthTests(OrthosCliTestCase):
    def test_login(self):
        """
        Test to verify that a login to the Orthos server can work. Assumes "admin"/"admin" is present.
        """
        # Arrange
        self.start_cli(username="admin")

        # Act
        self.process.sendline("auth")
        self.process.expect("Orthos password for admin:")
        self.process.sendline("admin")

        # Assert
        self.process.expect("(orthos 2.0.0:admin)")
        self.stop_cli()


if __name__ == '__main__':
    unittest.main()
