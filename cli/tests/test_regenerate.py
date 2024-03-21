"""
Tests that are verifying that all functionality that is related to the "regenerate" command is working.
"""

import unittest

from . import OrthosCliTestCase


class RegenerateTests(OrthosCliTestCase):
    @unittest.skip("Too much setup at the moment")
    def test_regenerate(self):
        self.assertTrue(False)


if __name__ == '__main__':
    unittest.main()
