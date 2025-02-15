import logging
import random
import smtplib
import socket
import subprocess
import textwrap
from datetime import date, datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from typing import TYPE_CHECKING, Any, List, NamedTuple, Optional, Tuple, Type, Union

import validators  # type: ignore
from django import forms
from django.conf import settings

if TYPE_CHECKING:
    from django.db import models

logger = logging.getLogger("utils")


class Serializer:
    class Format:
        JSON = "json"
        YAML = "yaml"

        @classmethod
        def is_valid(cls, output_format: str) -> bool:
            """Check if `output_format` is valid."""
            return output_format.lower() in {cls.JSON, cls.YAML}


def get_domain(fqdn: str) -> str:
    """Return domain of FQDN."""
    return ".".join(fqdn.split(".")[1:])


def get_hostname(fqdn: str) -> str:
    """Return hostname of FQDN."""
    return fqdn.split(".")[0]


class DNSLookupTuple(NamedTuple):
    """
    Describes a DNS lookup done by the application.
    """

    ipv4: List[str]
    ipv6: List[str]


def get_ip(fqdn: str, ip_version: int = 4) -> Optional[DNSLookupTuple]:
    """
    Return all IP addresses for FQDN.

    Use `ip_version` to specify which IP version gets returned.

    IP versions (`ip_version`):
        4  - ['192.168.0.1', ...]
        6  - ['0:0:0:0:0:ffff:c0a8:1', ...]
        10 - (['192.168.0.1', ...], [0:0:0:0:0:ffff:c0a8:1, ...])
    """
    ipv4: List[str] = []
    ipv6: List[str] = []

    try:
        result = socket.getaddrinfo(fqdn, None, 0, socket.SOCK_STREAM, socket.SOL_TCP)

        for address_family in result:
            if address_family[0] == socket.AF_INET:
                ipv4.append(address_family[4][0])
            elif address_family[0] == socket.AF_INET6:
                ipv6.append(address_family[4][0])
    except (IndexError, socket.gaierror) as e:
        logger.exception(
            "DNS lookup for '%s': NXDOMAIN (non-existing domain) (%s)", fqdn, str(e)
        )
        return None

    if not ipv4:
        logger.error("FQDN '%s' doesn't have any IPv4 address!", fqdn)
        return None

    if ip_version == 4:
        return DNSLookupTuple(ipv4, [])
    elif ip_version == 6:
        return DNSLookupTuple([], ipv6)
    elif ip_version == 10:
        return DNSLookupTuple(ipv4, ipv6)
    else:
        raise ValueError("Unknown IP version '{}'!".format(ip_version))


def get_ipv4(fqdn: str) -> Optional[str]:
    """Return (first) IPv4 address for FQDN."""
    lookup_result = get_ip(fqdn, ip_version=4)
    if lookup_result and lookup_result.ipv4:
        return lookup_result.ipv4[0]
    return None


def get_ipv6(fqdn: str) -> Optional[str]:
    """Return (first) IPv6 address for FQDN."""
    lookup_result = get_ip(fqdn, ip_version=6)
    if lookup_result and lookup_result.ipv6:
        return lookup_result.ipv6[0]
    return None


def is_dns_resolvable(fqdn: str) -> bool:
    """Check if FQDN can be resolved by DNS server."""
    if not fqdn:
        return False

    try:
        socket.gethostbyname(fqdn)
        return True
    except socket.error:
        return False


def has_valid_domain_ending(
    fqdn: str, valid_endings: Optional[Union[str, List[str]]]
) -> bool:
    """
    Check if FQDN has valid domain ending. This check can be bypassed if no
    valid domain endings are given.

    Example:
        example.de
        example.com
    """
    if valid_endings is None:
        return True

    if isinstance(valid_endings, str):
        valid_endings = [valid_endings]

    for domain in valid_endings:
        if fqdn.endswith(domain):
            return True
    return False


def wrap80(text: str) -> str:
    """Wrap the text at the given column."""
    return "\n".join(textwrap.wrap(text, width=80))


def is_valid_mac_address(mac_address: str) -> bool:
    """
    Check if MAC address is valid.

    Example:
        00:11:22:33:44:55
    """
    if validators.mac_address(mac_address):
        return True

    return False


def str_time_to_datetime(time: str) -> Optional[datetime]:
    """
    Convert string time (24-hour) to datetime object.

    Example:
        '12:34'
    """
    try:
        return datetime.strptime(time, "%H:%M")
    except ValueError:
        pass
    return None


def send_email(
    to_addr: str, subject: str, message: str, from_addr: Optional[str] = None
) -> None:
    """Send an email."""
    from orthos2.data.models import ServerConfig

    if not ServerConfig.objects.bool_by_key("orthos.debug.mail.send"):
        logger.warning("Disabled: set 'orthos.debug.mail.send' to 'true'")
        return

    try:
        if from_addr is None:
            from_addr = ServerConfig.objects.by_key("mail.from.address")

        msg = MIMEMultipart()
        msg["To"] = to_addr
        msg["X-BeenThere"] = "orthos"
        msg["From"] = from_addr
        subject_prefix = ServerConfig.objects.by_key("mail.subject.prefix")
        if subject_prefix:
            msg["Subject"] = subject_prefix + subject
        else:
            msg["Subject"] = subject
        text = MIMEText(message)
        text.add_header("Content-Disposition", "inline")
        msg["Date"] = formatdate(localtime=True)
        msg.attach(text)

        relay_fqdn = ServerConfig.objects.by_key("mail.smtprelay.fqdn")
        if relay_fqdn is None:
            raise ValueError(
                'Please configure your SMTP relay via the ServerConfig key "mail.smtprelay.fqdn"!'
            )
        s = smtplib.SMTP(relay_fqdn)
        logger.info("Sending mail to '%s' (subject: '%s')", msg["To"], msg["Subject"])
        s.sendmail(msg["From"], [to_addr], msg.as_string())
        s.quit()
    except Exception:
        logger.exception("Something went wrong while sending E-Mail!")


def execute(command: str) -> Tuple[str, str, int]:
    """
    Execute a (local) command and returns stdout, stderr and exit status.

    With `shell=True` the command needs to be a string. Otherwise the first element is set as shell
    which leads to issues.
    """
    result = ("", "", 1)

    try:
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
        )
        data = process.communicate()

        # stdout, stderr, exitcode
        result = data[0].decode("utf-8"), data[1].decode("utf-8"), process.returncode
    except FileNotFoundError:
        logger.exception("No such file or directory: %s", command)
    except Exception as e:
        logger.exception(e)

    return result


def get_s390_hostname(hostname: str, use_uppercase: bool = True) -> Optional[str]:
    """Return the 'linux...' name of the s390 machine."""
    if use_uppercase:
        linux = "LINUX"
    else:
        linux = "linux"

    if not isinstance(hostname, str) or len(hostname) < 10:
        logger.error("Invalid s390 name: %s", hostname)
        return None
    else:
        name = hostname[7:10]
    logging.debug("s390 name conversion from %s to %s", hostname, linux + name)
    return linux + name


def sync(original: "models.Model", temp: "models.Model") -> None:
    """Synchronize attributes between two model objects."""
    if type(original) is not type(temp):
        return

    differences: List[str] = []

    for key in temp.__dict__.keys():
        if (
            not key.startswith("_")
            and original.__class__().__dict__[key] != temp.__dict__[key]
        ):
            differences.append(key)

    logger.debug("Set values for '%s': %s", original, ", ".join(differences))

    original.refresh_from_db()

    for key in differences:
        original.__dict__[key] = temp.__dict__[key]

    original.save()


def add_offset_to_date(
    offset: float, begin: date = date.today(), as_string: bool = False
) -> Union[date, str]:
    """
    Add the day offset to begin date (default: today).

    Returns either a datetime.date object or a valid date string.

    Example:
        25      datetime.date(2017, 12, 24)     -> datetime.date(2018, 1, 18)
        ^       ^                               -> '2018-01-18'
        offset  begin
    """
    from django.utils.formats import date_format

    date = begin + timedelta(days=offset)

    if as_string:
        return str(date_format(date, format=settings.SHORT_DATE_FORMAT))

    return date


def get_random_mac_address() -> str:
    """Return a random MAC Address (local unicast)."""
    # TODO: This comment is wrong.
    # Xen Vendor OUI is 00:16:3e
    # KVM Vendor OUI is 52:54:00
    #
    # oct1:   locally administered+unicast    01000010 => 0x42
    # oct2-4: 52:54:00 because this is default KVM Vendor OUI
    # oct5-6: randomized
    #
    # This way we avoid running into conflicts with non-Orthos-created KVM machines.
    mac = [
        0x52,
        0x54,
        0x00,
        0x42,
        random.randint(0x00, 0xFF),
        random.randint(0x00, 0xFF),
    ]
    mac_address = ":".join(map(lambda x: "{:02x}".format(x), mac))
    return mac_address.upper()


def normalize_ascii(string: str) -> str:
    """
    Remove non-ascii characters of a string.

    In that case, the character is set to ` ` (space).
    """
    result = ""
    for char in string:
        result += char if (ord(char) > 0 and ord(char) < 127) else " "
    return result


def format_cli_form_errors(form: forms.Form) -> str:
    """Format form errors for CLI."""
    output = ""
    for field_name, errors in form.errors.items():
        if field_name in form.fields:
            label = form.fields[field_name].label
            if not label:
                label = field_name.capitalize()
        else:
            label = "*"

        for error in errors:
            output += "* {} [{}]\n".format(error, label)
    return output.rstrip("\n")


def safe_get_or_default(
    model: Type["models.Model"],
    key: str,
    value: str,
    field: str,
    default: Any = None,
) -> Any:
    """
    Allow access to a `field` of a specified `model`.

    `key` and `value` is needed for filtering down to the expected object. If there is no object,
    multiple objects or any other exception, `default` gets returned.
    """
    try:
        # Any model has a dynamic objects attribute at runtime.
        return getattr(model.objects.get(**{key: value}), field)  # type: ignore
    except Exception:
        pass
    return default
