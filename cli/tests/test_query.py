"""
Tests that are verifying that all functionality that is related to the "query" command is working.
"""

import unittest

from . import OrthosCliTestCase


class QueryTests(OrthosCliTestCase):
    @unittest.skip("Too much setup at the moment")
    def test_query_fields(self):
        # Arrange
        self.start_cli(username="admin")

        # Act
        self.process.sendline("query fqdn")

        # Cleanup
        self.stop_cli()

        # Assert
        self.assertTrue(False)

    @unittest.skip("Too much setup at the moment")
    def test_query_fields_where(self):
        # Arrange
        self.start_cli(username="admin")

        # Act
        self.process.sendline("query fqdn where cpu_model =~ Intel")

        # Cleanup
        self.stop_cli()

        # Assert
        self.assertTrue(False)


if __name__ == '__main__':
    unittest.main()
