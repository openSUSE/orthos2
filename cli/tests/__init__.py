"""
This module contains integration tests for the Python CLI. Unit-Testing doesn't make much sense as there
is no logic client side for specific endpoints.
"""
import pathlib
import unittest

import pexpect


class OrthosCliTestCase(unittest.TestCase):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName=methodName)
        self.process = None

    @classmethod
    def setUpClass(cls):
        pathlib.Path("~orthos/.config").expanduser().mkdir(exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        config_folder = pathlib.Path("~orthos/.config").expanduser()
        config_file = config_folder / "orthosrc"
        config_file.unlink(missing_ok=True)
        if config_folder.exists():
            config_folder.rmdir()

    def start_cli(self, username=""):
        """
        Starts the CLI and tests if the startup of it has occurred orderly.
        """
        # Build path were the code of the CLI is present. Don't use the globally installed one!
        cli_location = pathlib.Path(__file__).parent.parent / "orthos2"
        cli_command = str(cli_location) + " -P 8000"
        if username:
            cli_command += f" -U {username}"
        # Connect to local Orthos
        self.process = pexpect.spawn(cli_command)
        # Warning for http - WARNING:root:No secure ssl connection ...
        self.process.expect(r"WARNING:root:No secure ssl connection.*\r\n")
        # Shell prefix
        self.process.expect(r"\(orthos 2.0.0:Anonymous\) ")

    def login_cli(self):
        """
        Assumes a started CLI and logs in the "admin"/"admin" user.
        """
        self.process.sendline("auth")
        self.process.expect("Orthos password for admin:")
        self.process.sendline("admin")
        # Check login was successful
        self.process.expect("(orthos 2.0.0:admin)")

    def stop_cli(self) -> bool:
        """
        Stops the CLI and returns if the program exited correctly.
        """
        # Exit application
        self.process.sendline("quit")
        # Exit message
        self.process.expect("Good bye, have a lot of fun...")
        # Wait until the process has exited
        self.process.wait()
        # Exit code 0
        return self.process.exitstatus == 0
