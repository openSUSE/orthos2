import logging
from unittest import mock

from django.test import TestCase

from orthos2.data.models.architecture import Architecture
from orthos2.data.models.domain import Domain
from orthos2.data.models.machine import Machine
from orthos2.data.models.networkinterface import NetworkInterface
from orthos2.data.models.serverconfig import ServerConfig
from orthos2.data.models.system import System
from orthos2.utils.machinechecks import nmap_check, ping_check
from orthos2.utils.misc import (
    execute,
    get_domain,
    get_hostname,
    has_valid_domain_ending,
    is_dns_resolvable,
    normalize_ascii,
    str_time_to_datetime,
    suggest_host_ip,
)

logging.disable(logging.CRITICAL)


class MiscMethodTests(TestCase):
    def test_get_domain(self) -> None:
        """get_domain() should return the domain for a given FQDN."""
        fqdn = "foo.bar"
        assert get_domain(fqdn) == "bar"

        fqdn = "foo.bar.suse.de"
        assert get_domain(fqdn) == "bar.suse.de"

        fqdn = "foo.bar.foobar.suse.de"
        assert get_domain(fqdn) == "bar.foobar.suse.de"

    def test_get_hostname(self) -> None:
        """get_hostname() should return the hostname for a given FQDN."""
        fqdn = "foo.bar"
        assert get_hostname(fqdn) == "foo"

        fqdn = "foo.bar.suse.de"
        assert get_hostname(fqdn) == "foo"

        fqdn = "foo.bar.foobar.suse.de"
        assert get_hostname(fqdn) == "foo"

    @mock.patch("orthos2.utils.misc.socket.gethostbyname")
    def test_is_dns_resolvable(self, mocked_gethostbyname) -> None:
        """is_dns_resolvable() should return True if a FQDN is resolvable, False otherwise."""
        import socket

        fqdn = "foo.bar.suse.de"
        mocked_gethostbyname.return_value = "192.168.0.1"
        assert is_dns_resolvable(fqdn) is True

        mocked_gethostbyname.side_effect = socket.gaierror()
        assert is_dns_resolvable(fqdn) is False

    def test_has_valid_domain_ending(self) -> None:
        """
        has_valid_domain_ending() should return True if given FQDN has a valid domain ending,
        False otherwise.
        """
        assert has_valid_domain_ending("test.foo", "foo") is True
        assert has_valid_domain_ending("test.foo.bar", "foo.bar") is True
        assert has_valid_domain_ending("test.foo", ["foo"]) is True
        assert has_valid_domain_ending("test.foo", ["bar", "foo"]) is True

        assert has_valid_domain_ending("test.foo", []) is False
        assert has_valid_domain_ending("test.foo", ["bar"]) is False

    def test_str_time_to_datetime(self) -> None:
        """
        str_time_to_datetime() should return a valid datetime.datetime object, None otherwise.
        """
        from datetime import datetime

        assert str_time_to_datetime("") is None
        assert str_time_to_datetime("foo") is None
        assert str_time_to_datetime("12:34") == datetime(1900, 1, 1, 12, 34)


class MiscSuggestIpTests(TestCase):
    def setUp(self) -> None:
        ServerConfig(
            key="domain.validendings", value="example.de, example.com, foo.de"
        ).save()

        self.domain = Domain(
            name="example.de",
            ip_v4="192.168.178.0",
            ip_v6="fe80:0:0:1::",
            subnet_mask_v4=29,
            subnet_mask_v6=64,
            dynamic_range_v4_start="192.168.178.6",
            dynamic_range_v4_end="192.168.178.6",
            dynamic_range_v6_start="fe80:0:0:1::6",
            dynamic_range_v6_end="fe80:0:0:1:ffff:ffff:ffff:fffe",
        )
        self.domain.save()

        self.sys = System(name="Bare Metal")
        self.sys.save()

        self.arch = Architecture(name="foobar64")
        self.arch.save()

        self.machine = Machine(
            fqdn="test.example.de", system=self.sys, architecture=self.arch
        )
        self.machine.save()

        for i in range(1, 5):
            NetworkInterface(
                ip_address_v4=f"192.168.178.{i}",
                ip_address_v6=f"fe80:0:0:1::{i}",
                mac_address=f"AA:BB:CC:DD:EE:F{i}",
                machine=self.machine,
            ).save()

    def test_suggest_host_ip_v4(self) -> None:
        """
        suggest_host_ip() should return a valid IP address.
        """
        # Act
        suggested_ip = suggest_host_ip(4, self.domain)
        # Assert
        self.assertEqual(suggested_ip, "192.168.178.5")

    def test_suggest_host_ip_full_network_v4(self) -> None:
        """
        suggest_host_ip() should return the localhost address if the network has no free host addresses.
        """
        # Arrange
        NetworkInterface(
            ip_address_v4="192.168.178.5",
            mac_address="AA:BB:CC:DD:EE:F5",
            machine=self.machine,
        ).save()
        # Act
        suggested_ip = suggest_host_ip(4, self.domain)
        # Assert
        self.assertEqual(suggested_ip, "127.0.0.1")

    def test_suggest_host_ip_v6(self) -> None:
        """
        suggest_host_ip() should return a valid IP address.
        """
        # Act
        suggested_ip = suggest_host_ip(6, self.domain)
        # Assert
        self.assertEqual(suggested_ip, "fe80:0:0:1::5")

    def test_suggest_host_ip_full_network_v6(self) -> None:
        """
        suggest_host_ip() should return the localhost address because everything is blocked by the dynamic range.
        """
        # Arrange
        NetworkInterface(
            ip_address_v6="fe80:0:0:1::5",
            mac_address="AA:BB:CC:DD:EE:F5",
            machine=self.machine,
        ).save()
        # Act
        suggested_ip = suggest_host_ip(6, self.domain)
        # Assert
        self.assertEqual(suggested_ip, "::1")


class ChecksMethodTests(TestCase):
    @mock.patch("orthos2.utils.misc.subprocess.Popen")
    def test_ping_check(self, mocked_popen):
        """ping_check() should return True if a FQDN is pingable, False otherwise."""
        fqdn = "foo.bar.suse.de"
        mocked_popen.return_value.returncode = 0
        assert ping_check(fqdn) is True

        mocked_popen.return_value.returncode = 1
        assert ping_check(fqdn) is False

    @mock.patch("orthos2.utils.machinechecks.socket.socket.connect")
    @mock.patch("orthos2.utils.machinechecks.ping_check")
    def test_nmap_check(self, mocked_ping_check, mocked_connect):
        """nmap_check() should return True if a host runs SSH, False otherwise."""
        import socket

        fqdn = "foo.bar.suse.de"
        mocked_ping_check.return_value = False
        mocked_connect.return_value = True
        assert nmap_check(fqdn) is False

        mocked_ping_check.return_value = True
        mocked_connect.side_effect = socket.error
        assert nmap_check(fqdn) is False

        mocked_ping_check.return_value = True
        mocked_connect.return_value = socket.socket.connect

    #         assert nmap_check(fqdn) == True

    def test_execute(self) -> None:
        """execute() should return a tuple with the output and the exit status code."""
        result = execute("foobar -baz")
        assert result[0] == ""
        assert result[2] == 127

        result = execute("echo foo")
        assert result[0] == "foo\n"
        assert result[2] == 0

    def test_normalize_ascii(self) -> None:
        """
        normalize_ascii() should only return a string containing ascii characters with decimal
        codes between 1 and 127. All other codes are translated to space.
        """
        string = ""
        for i in range(1, 256):
            string += chr(i)

        self.assertEqual(len(string), 255)

        string = normalize_ascii(string)

        self.assertEqual(len(string), 255)

        for char in string:
            self.assertTrue(ord(char) > 0)
            self.assertTrue(ord(char) < 127)
