"""
Tests that are verifying that all functionality that is related to the "reservationhistory" command is working.
"""

import unittest

from . import OrthosCliTestCase


class ReservationhistoryTests(OrthosCliTestCase):
    @unittest.skip("Too much setup at the moment")
    def test_reserverationhistory(self):
        # Arrange
        self.start_cli()

        # Act
        self.process.sendline("reservationhistory <fqdn>")

        # Cleanup
        self.stop_cli()

        # Assert
        self.assertTrue(False)


if __name__ == '__main__':
    unittest.main()
