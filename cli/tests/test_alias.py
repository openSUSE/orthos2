"""
Tests that are verifying that all functionality that is related to the "alias" command is working.
"""

import pathlib
import unittest

from . import OrthosCliTestCase


class AliasTests(OrthosCliTestCase):
    def test_add(self):
        """
        Test to verify that adding aliases via CLI is working.
        """
        # Arrange
        expected = "test = query name"
        self.start_cli()
        # Uncomment the following line to debug the test
        # self.process.logfile = sys.stdout.buffer

        # Act
        self.process.sendline("alias test query name")
        self.process.expect("(orthos 2.0.0:Anonymous)")

        # Assert
        self.stop_cli()
        config_file = pathlib.Path("~orthos/.config/orthosrc").expanduser()
        config_file_content = config_file.read_text().split("\n")
        # The file is not present
        self.assertEqual(config_file_content[1], expected)


if __name__ == "__main__":
    unittest.main()
