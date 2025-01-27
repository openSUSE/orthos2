"""
Tests that are verifying that all functionality that is related to the "add" command is working.
"""

import unittest

from . import OrthosCliTestCase


class AddTests(OrthosCliTestCase):
    def test_add_bmc_negative(self) -> None:
        """
        Test to verify that adding a BMC via CLI is working. Assumes "admin"/"admin" is present.
        """
        # Arrange
        expected = "ERROR: Machine '<fqdn>' does not exist!"
        self.start_cli(username="admin")
        self.login_cli()
        # Uncomment the following line to debug the test
        # self.process.logfile = sys.stdout.buffer

        # Act
        if self.process is None:
            self.fail("CLI process not successfully spawned!")
        self.process.sendline("add bmc <fqdn>")
        self.process.expect("(orthos 2.3.0:admin)")
        if self.process.before is None:
            self.fail("CLI didn't communicate back properly!")
        output = self.process_output(self.process.before)

        # Assert
        # FIXME: This is a negative test atm
        self.stop_cli()
        # The CLI prints out "Please wait..." and uses carriage return to hide the message once the result is returned.
        messages = output[0].split("\r")
        self.assertEqual(len(messages), 4)
        self.assertEqual(messages[2], expected)

    @unittest.skip("Too much setup at the moment")
    def test_add_bmc_positive(self) -> None:
        """
        Test to verify that adding a BMC via CLI is working with valid inputs. Assumes "admin"/"admin" is present.
        """
        # Arrange
        expected = "Success"
        self.start_cli(username="admin")
        self.login_cli()
        # Uncomment the following line to debug the test
        # self.process.logfile = sys.stdout.buffer
        # TODO: Add architecture - not possible via CLI
        # TODO: Add Domain - not possible via CLI
        # TODO: Add machine (fqdn, arch, system)

        # Act
        if self.process is None:
            self.fail("CLI process not successfully spawned!")
        self.process.sendline("add bmc <fqdn>")
        self.process.expect("(orthos 2.3.0:admin)")
        if self.process.before is None:
            self.fail("CLI didn't communicate back properly!")
        output = self.process_output(self.process.before)

        # Assert
        self.stop_cli()
        # The CLI prints out "Please wait..." and uses carriage return to hide the message once the result is returned.
        messages = output[0].split("\r")
        self.assertEqual(len(messages), 4)
        self.assertEqual(messages[2], expected)
        assert False
