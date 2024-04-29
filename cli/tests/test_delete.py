"""
Tests that are verifying that all functionality that is related to the "delete" command is working.
"""

import unittest

from . import OrthosCliTestCase


class DeleteTests(OrthosCliTestCase):
    @unittest.skip("Too much setup at the moment")
    def test_delete(self) -> None:
        self.assertTrue(False)
