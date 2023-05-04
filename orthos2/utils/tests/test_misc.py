import logging

import mock
from django.test import TestCase

from orthos2.utils.machinechecks import nmap_check, ping_check
from orthos2.utils.misc import (execute, get_domain, get_hostname,
                                has_valid_domain_ending, is_dns_resolvable,
                                is_valid_mac_address, normalize_ascii,
                                str_time_to_datetime)

logging.disable(logging.CRITICAL)


class MiscMethodTests(TestCase):

    def test_get_domain(self):
        """get_domain() should return the domain for a given FQDN."""
        fqdn = 'foo.bar'
        assert get_domain(fqdn) == 'bar'

        fqdn = 'foo.bar.suse.de'
        assert get_domain(fqdn) == 'bar.suse.de'

        fqdn = 'foo.bar.foobar.suse.de'
        assert get_domain(fqdn) == 'bar.foobar.suse.de'

    def test_get_hostname(self):
        """get_hostname() should return the hostname for a given FQDN."""
        fqdn = 'foo.bar'
        assert get_hostname(fqdn) == 'foo'

        fqdn = 'foo.bar.suse.de'
        assert get_hostname(fqdn) == 'foo'

        fqdn = 'foo.bar.foobar.suse.de'
        assert get_hostname(fqdn) == 'foo'

    @mock.patch('utils.misc.socket.gethostbyname')
    def test_is_dns_resolvable(self, mocked_gethostbyname):
        """is_dns_resolvable() should return True if a FQDN is resolvable, False otherwise."""
        import socket

        fqdn = 'foo.bar.suse.de'
        mocked_gethostbyname.return_value = '192.168.0.1'
        assert is_dns_resolvable(fqdn) is True

        mocked_gethostbyname.side_effect = socket.gaierror()
        assert is_dns_resolvable(fqdn) is False

    def test_has_valid_domain_ending(self):
        """
        has_valid_domain_ending() should return True if given FQDN has a valid domain ending,
        False otherwise.
        """
        assert has_valid_domain_ending('test.foo', 'foo') is True
        assert has_valid_domain_ending('test.foo.bar', 'foo.bar') is True
        assert has_valid_domain_ending('test.foo', ['foo']) is True
        assert has_valid_domain_ending('test.foo', ['bar', 'foo']) is True

        assert has_valid_domain_ending('test.foo', []) is False
        assert has_valid_domain_ending('test.foo', ['bar']) is False

    def test_is_valid_mac_address(self):
        """
        is_valid_mac_address() should return True if given MAC address is valid, False otherwise.
        """
        assert is_valid_mac_address('') is False
        assert is_valid_mac_address('foo') is False

        assert is_valid_mac_address('12:34:56:78:9A:BC') is True
        assert is_valid_mac_address('12:34:56:78:9A:BC:D') is False

    def test_str_time_to_datetime(self):
        """
        str_time_to_datetime() should return a valid datetime.datetime object, None otherwise.
        """
        from datetime import datetime

        assert str_time_to_datetime('') is None
        assert str_time_to_datetime('foo') is None
        assert str_time_to_datetime('12:34') == datetime(1900, 1, 1, 12, 34)


class ChecksMethodTests(TestCase):

    @mock.patch('utils.misc.subprocess.Popen')
    def test_ping_check(self, mocked_popen):
        """ping_check() should return True if a FQDN is pingable, False otherwise."""
        fqdn = 'foo.bar.suse.de'
        mocked_popen.return_value.returncode = 0
        assert ping_check(fqdn) is True

        mocked_popen.return_value.returncode = 1
        assert ping_check(fqdn) is False

    @mock.patch('utils.machinechecks.socket.socket.connect')
    @mock.patch('utils.machinechecks.ping_check')
    def test_nmap_check(self, mocked_ping_check, mocked_connect):
        """nmap_check() should return True if a host runs SSH, False otherwise."""
        import socket

        fqdn = 'foo.bar.suse.de'
        mocked_ping_check.return_value = False
        mocked_connect.return_value = True
        assert nmap_check(fqdn) is False

        mocked_ping_check.return_value = True
        mocked_connect.side_effect = socket.error
        assert nmap_check(fqdn) is False

        mocked_ping_check.return_value = True
        mocked_connect.return_value = socket.socket.connect
#         assert nmap_check(fqdn) == True

    def test_execute(self):
        """execute() should return a tuple with the output and the exit status code."""
        result = execute('foobar -baz')
        assert result[0] == ''
        assert result[2] == 127

        result = execute('echo foo')
        assert result[0] == 'foo\n'
        assert result[2] == 0

    def test_normalize_ascii(self):
        """
        normalize_ascii() should only return a string containing ascii characters with decimal
        codes between 1 and 127. All other codes are translated to space.
        """
        string = ''
        for i in range(1, 256):
            string += chr(i)

        self.assertEqual(len(string), 255)

        string = normalize_ascii(string)

        self.assertEqual(len(string), 255)

        for char in string:
            self.assertTrue(ord(char) > 0)
            self.assertTrue(ord(char) < 127)
