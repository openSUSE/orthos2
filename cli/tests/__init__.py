"""
This module contains integration tests for the Python CLI. Unit-Testing doesn't make much sense as there
is no logic client side for specific endpoints.
"""

# mypy: warn-unused-ignores=False

import pathlib
import unittest
from typing import AnyStr, List, Optional

import pexpect


class OrthosCliTestCase(unittest.TestCase):
    def __init__(self, methodName: str = "runTest") -> None:
        super().__init__(methodName=methodName)
        self.process: Optional[pexpect.spawn[str]] = None

    @classmethod
    def setUpClass(cls) -> None:
        pathlib.Path("~orthos/.config").expanduser().mkdir(exist_ok=True)

    @classmethod
    def tearDownClass(cls) -> None:
        config_folder = pathlib.Path("~orthos/.config").expanduser()
        config_file = config_folder / "orthosrc"
        config_file.unlink(missing_ok=True)
        if config_folder.exists():
            config_folder.rmdir()

    def start_cli(self, username: str = "") -> None:
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
        self.process.expect(r"\(orthos 2.3.0:Anonymous\) ")

    def login_cli(self) -> None:
        """
        Assumes a started CLI and logs in the "admin"/"admin" user.
        """
        if self.process is None:
            raise RuntimeError("CLI process not successfully spawned!")
        self.process.sendline("auth")
        self.process.expect("Orthos password for admin:")
        self.process.sendline("admin")
        # Check login was successful
        self.process.expect("(orthos 2.3.0:admin)")

    def stop_cli(self) -> bool:
        """
        Stops the CLI and returns if the program exited correctly.
        """
        if self.process is None:
            raise RuntimeError("CLI process not successfully spawned!")
        # Exit application
        self.process.sendline("quit")
        # Exit message
        self.process.expect("Good bye, have a lot of fun...")
        # Wait until the process has exited
        self.process.wait()
        # Exit code 0
        # https://github.com/python/typeshed/issues/13200
        return self.process.exitstatus == 0

    @staticmethod
    def process_output(output: AnyStr) -> List[str]:
        """
        Process the output from the CLI and decode it in case it is of type byte.

        :param output: The output from the CLI.
        :returns: Each element in the list represents a single line.
        """
        if isinstance(output, bytes):
            result = output.decode("utf-8")
        elif isinstance(output, str):  # type: ignore
            result = output
        else:
            result = ""
        return result.split("\n")[1:]
