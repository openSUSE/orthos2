"""
Module for testing the functionality of the help command.
"""

import re
import unittest

from . import OrthosCliTestCase


class HelpTests(OrthosCliTestCase):
    def test_no_topic(self) -> None:
        """
        Test to verify that all help topics are listed on the CLI.
        """
        # Arrange
        self.start_cli()

        # Act
        if self.process is None:
            self.fail("CLI process not successfully spawned!")
        self.process.sendline("HELP")
        self.process.expect(r"\(orthos 2.3.0:Anonymous\) ")
        if self.process.before is None:
            self.fail("CLI didn't communicate back properly!")
        output = self.process_output(self.process.before)

        # Assert
        self.stop_cli()
        self.assertEqual(output[0], "Commands are:\r")
        for line in output[2:19]:
            self.assertIsNotNone(
                re.match(r"^\t[A-Z]+\s", line),
                msg="Line didn't start with tab and capslock!",
            )
        # 20 lines + the line the shell starts to match again
        self.assertEqual(len(output), 21)

    @unittest.skip("Too much setup at the moment")
    def test_topic_info(self) -> None:
        # Single line of text
        # empty line
        # Usage
        # Empty line
        # Arguments
        # Empty Line
        # Example
        # Empty Line
        self.assertTrue(False)

    @unittest.skip("Too much setup at the moment")
    def test_topic_query(self) -> None:
        # Two lines of text
        # Empty line
        # Example
        # Empty Line
        # "Valid operators are
        # Line of dashes
        # Operator listing
        # Line of dashes
        self.assertTrue(False)

    @unittest.skip("Too much setup at the moment")
    def test_topic_reserve(self) -> None:
        # Single line of text
        # empty line
        # Usage
        # Empty line
        # Arguments
        # Empty Line
        # Example
        # Empty Line
        self.assertTrue(False)

    @unittest.skip("Too much setup at the moment")
    def test_topic_release(self) -> None:
        # Single line of text
        # empty line
        # Usage
        # Empty line
        # Arguments
        # Empty Line
        # Example
        # Empty Line
        self.assertTrue(False)

    @unittest.skip("Too much setup at the moment")
    def test_topic_reservationhistory(self) -> None:
        # Single line of text
        # empty line
        # Usage
        # Empty line
        # Arguments
        # Empty Line
        # Example
        # Empty Line
        self.assertTrue(False)

    @unittest.skip("Too much setup at the moment")
    def test_topic_rescan(self) -> None:
        # three lines of text
        # empty line
        # Usage
        # Empty line
        # Arguments
        # Empty Line
        # Example
        # Empty Line
        self.assertTrue(False)

    @unittest.skip("Too much setup at the moment")
    def test_topic_regenerate(self) -> None:
        # Two lines of text
        # empty line
        # Usage
        # Empty line
        # Arguments
        # Empty Line
        # Example
        # Empty Line
        self.assertTrue(False)

    @unittest.skip("Too much setup at the moment")
    def test_topic_serverconfig(self) -> None:
        # Single line of text
        # empty line
        # Usage
        # Empty line
        # Arguments
        # Empty Line
        # Example
        # Empty Line
        self.assertTrue(False)

    @unittest.skip("Too much setup at the moment")
    def test_topic_setup(self) -> None:
        # Single line of text
        # empty line
        # Usage
        # Empty line
        # Arguments
        # Empty Line
        # Example
        # Empty Line
        self.assertTrue(False)

    @unittest.skip("Too much setup at the moment")
    def test_topic_power(self) -> None:
        # Single line of text
        # empty line
        # Usage
        # Empty line
        # Arguments
        # Empty Line
        # Example
        # Empty Line
        self.assertTrue(False)

    @unittest.skip("Too much setup at the moment")
    def test_topic_add(self) -> None:
        # Single line of text
        # empty line
        # Usage
        # Empty line
        # Arguments
        # Empty Line
        # Example
        # Empty Line
        self.assertTrue(False)

    @unittest.skip("Too much setup at the moment")
    def test_topic_delete(self) -> None:
        # Single line of text
        # empty line
        # Usage
        # Empty line
        # Arguments
        # Empty Line
        # Example
        # Empty Line
        self.assertTrue(False)

    @unittest.skip("Too much setup at the moment")
    def test_topic_alias(self) -> None:
        # Five lines of text
        # Empty line
        # One line of text
        # empty Line
        # Usage
        # Empty line
        # Arguments
        # Empty line
        # Example
        # Empty Line
        # Example continued
        # Empty Line
        self.assertTrue(False)

    def test_topic_auth(self) -> None:
        # Arrange
        expected_output = "No help available!"
        self.start_cli()

        # Act
        if self.process is None:
            self.fail("CLI process not successfully spawned!")
        self.process.sendline("HELP auth")

        # Assert
        self.process.expect(expected_output)
        self.stop_cli()

    def test_topic_exit(self) -> None:
        # Arrange
        expected_output = "No help available!"
        self.start_cli()

        # Act
        if self.process is None:
            self.fail("CLI process not successfully spawned!")
        self.process.sendline("HELP exit")

        # Assert
        self.process.expect(expected_output)
        self.stop_cli()

    def test_topic_config(self) -> None:
        # Arrange
        expected_output = "No help available!"
        self.start_cli()

        # Act
        if self.process is None:
            self.fail("CLI process not successfully spawned!")
        self.process.sendline("HELP config")

        # Assert
        self.process.expect(expected_output)
        self.stop_cli()

    def test_topic_help(self) -> None:
        # Arrange
        expected_output = "No help available!"
        self.start_cli()

        # Act
        if self.process is None:
            self.fail("CLI process not successfully spawned!")
        self.process.sendline("HELP help")

        # Assert
        self.process.expect(expected_output)
        self.stop_cli()
