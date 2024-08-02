"""
Tests that are verifying that all functionality that is related to the "serverconfig" command is working.
"""

import unittest

from . import OrthosCliTestCase


class ServerconfigTests(OrthosCliTestCase):
    @unittest.skip("Too much setup at the moment")
    def test_serverconfig(self):
        # Arrange
        self.start_cli(username="admin")
        self.login_cli()
        # Uncomment the following line to debug the test
        # self.process.logfile = sys.stdout.buffer

        # Act
        self.process.sendline("serverconfig")
        self.process.expect("")

        # Assert
        self.stop_cli()
        self.assertTrue(False)


if __name__ == "__main__":
    unittest.main()
