"""
Tests that are verifying that all functionality that is related to the "config" command is working.
"""

import unittest

from . import OrthosCliTestCase


class ConfigTests(OrthosCliTestCase):
    def test_config(self):
        """
        Test to verify that outputting the config of the CLI works as expected.
        """
        # Arrange
        self.start_cli()
        # Uncomment the following line to debug the test
        # self.process.logfile = sys.stdout.buffer

        # Act
        self.process.sendline("config")
        self.process.expect("(orthos 2.0.0:Anonymous)")
        output = self.process.before.decode().split("\n")[1:]

        # Assert
        self.stop_cli()
        self.assertEqual(len(output), 8)
        configuration = {}
        for _, item in enumerate(output[1:6]):
            tmp = item.strip("\r").split(":")
            configuration[tmp[0]] = tmp[1].strip("\t")
        self.assertEqual(len(configuration.keys()), 5)
        self.assertEqual(configuration.get("Port"), "8000")
        self.assertEqual(configuration.get("Server"), "localhost")
        self.assertEqual(configuration.get("User"), "Anonymous")
        self.assertEqual(configuration.get("Protocol"), "http")


if __name__ == '__main__':
    unittest.main()
