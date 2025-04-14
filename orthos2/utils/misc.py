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
from typing import TYPE_CHECKING, List, Literal, Optional, Tuple, Union

from django import forms
from django.conf import settings
from netaddr import IPAddress, IPNetwork

from orthos2.data.models.bmc import BMC
from orthos2.data.models.networkinterface import NetworkInterface

if TYPE_CHECKING:
    from django.db import models

    from orthos2.data.models.domain import Domain

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


def suggest_host_ip(protocol: Literal[4, 6], domain: "Domain") -> str:
    """
    Suggest a free IP address for a new network interface.
    """
    domain_ip = domain.ip_v4 if protocol == 4 else domain.ip_v6
    subnet = domain.subnet_mask_v4 if protocol == 4 else domain.subnet_mask_v6
    net = IPNetwork(f"{domain_ip}/{subnet}")
    # The size of the host part in bits
    host_size = int((32 if net.version == 4 else 128) - subnet)
    # The full network address as bits
    network_ip = int(net.ip)
    # The network part as bits
    network_ip_bits = network_ip >> host_size
    used_ips: set[IPAddress] = set()
    dyn_range_start = int(
        IPAddress(
            domain.dynamic_range_v4_start
            if protocol == 4
            else domain.dynamic_range_v6_start
        )
    )
    dyn_range_end = int(
        IPAddress(
            domain.dynamic_range_v4_end
            if protocol == 4
            else domain.dynamic_range_v6_end
        )
    )

    # Get all interfaces that match the network address
    intf_ip = IPAddress(0)
    for intf in NetworkInterface.objects.all():
        if protocol == 4:
            if not intf.ip_address_v4:
                continue
            intf_ip = IPAddress(intf.ip_address_v4, 4)
        if protocol == 6:
            if not intf.ip_address_v6:
                continue
            intf_ip = IPAddress(intf.ip_address_v6, 6)

        # Check if the bit representation of this interface's network address is the same.
        intf_ip_bits = int(intf_ip) >> host_size
        if intf_ip_bits == network_ip_bits:
            used_ips.add(intf_ip)

    bmc_ip = IPAddress(0)
    for bmc in BMC.objects.all():
        if protocol == 4:
            if not bmc.ip_address_v4:
                continue
            bmc_ip = IPAddress(bmc.ip_address_v4, 4)
        if protocol == 6:
            if not bmc.ip_address_v6:
                continue
            bmc_ip = IPAddress(bmc.ip_address_v6, 6)

        # Check if the bit representation of this interface's network address is the same.
        bmc_ip_bits = int(bmc_ip) >> host_size
        if bmc_ip_bits == network_ip_bits:
            used_ips.add(bmc_ip)

    idx = 0
    while idx < 2**host_size:
        # IP must not be inside the dynamic range.
        # Because this range can be huge, we skip over it when the current IP is inside this range.
        if network_ip + idx >= dyn_range_start and network_ip + idx <= dyn_range_end:
            idx += dyn_range_end
            continue

        next_ip = IPAddress(network_ip + idx)

        if (
            # IP must not be already in use.
            next_ip not in used_ips
            # IP must not be the network address.
            and next_ip != net.ip
            # IP must not be the broadcast address.
            and next_ip != net.broadcast
        ):
            return str(next_ip)
        idx += 1

    # If we get here, there aren't any free IPs left to give out. Return the default.
    return "127.0.0.1" if protocol == 4 else "::1"


def is_unique_mac_address(
    mac_address: str, exclude: Optional[List[str]] = None
) -> bool:
    """
    Check if `mac_address` does already exists.

    Exlcude all MAC addresses in `exclude`.
    """
    if exclude is None:
        exclude = []
    mac_addresses = NetworkInterface.objects.filter(mac_address=mac_address).exclude(
        mac_address__in=exclude
    )

    if mac_addresses.count() > 0:
        return False
    return True
