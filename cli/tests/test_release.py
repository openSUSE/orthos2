"""
Tests that are verifying that all functionality that is related to the "release" command is working.
"""

import unittest

from . import OrthosCliTestCase


class ReleaseTests(OrthosCliTestCase):
    @unittest.skip("Too much setup at the moment")
    def test_fqdn(self):
        # Assert
        self.assertTrue(False)

    @unittest.skip("Too much setup at the moment")
    def test_hostname(self):
        # Assert
        self.assertTrue(False)


if __name__ == "__main__":
    unittest.main()
