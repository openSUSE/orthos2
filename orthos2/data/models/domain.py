import collections
import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

from django.contrib import admin
from django.core import validators
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext as _

from orthos2.data.models.architecture import Architecture
from orthos2.data.models.serverconfig import ServerConfig
from orthos2.utils.cobbler import CobblerServer
from orthos2.utils.misc import has_valid_domain_ending

if TYPE_CHECKING:
    from orthos2.data.models.machine import Machine

logger = logging.getLogger("models")


def validate_domain_ending(value: str) -> None:
    valid_domain_endings = ServerConfig.objects.get_valid_domain_endings()
    if valid_domain_endings is None:
        raise ValidationError(
            "Valid domain endings could not be retrieved from settings."
        )

    if not has_valid_domain_ending(value, valid_domain_endings):
        raise ValidationError(
            "'{}' has no valid domain ending ({}).".format(
                value, ", ".join(valid_domain_endings)
            )
        )


class Domain(models.Model):
    class Manager(models.Manager["Domain"]):
        def get_by_natural_key(self, name: str) -> Optional["Domain"]:
            return self.get(name=name)

    name = models.CharField(
        max_length=200, blank=False, unique=True, validators=[validate_domain_ending]
    )

    cobbler_server = models.ForeignKey(
        "data.Machine",
        related_name="cobbler_server_for",
        verbose_name="Cobbler server",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        limit_choices_to={"administrative": True},
    )

    cobbler_server_username = models.CharField(
        default="cobbler",
        help_text="The username to login to Cobbler via XML-RPC.",
        verbose_name="Cobbler server username",
        max_length=255,
    )

    cobbler_server_password = models.CharField(
        default="cobbler",
        help_text="The password to login to Cobbler via XML-RPC.",
        verbose_name="Cobbler server password",
        max_length=255,
    )

    tftp_server = models.ForeignKey(
        "data.Machine",
        related_name="tftp_server_for_domain",
        verbose_name="TFTP server",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        limit_choices_to={"administrative": True},
    )

    cscreen_server = models.ForeignKey(
        "data.Machine",
        verbose_name="CScreen server",
        related_name="+",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={"administrative": True},
    )

    supported_architectures = models.ManyToManyField(  # type: ignore
        "data.Architecture",
        related_name="supported_domains",
        verbose_name="Supported architectures",
        through="DomainAdmin",
        blank=False,
    )

    ip_v4 = models.GenericIPAddressField(
        verbose_name=_("IPv4 address"),
        protocol="IPv4",
        help_text=_("The IPv4 address of the network."),
    )

    ip_v6 = models.GenericIPAddressField(
        verbose_name=_("IPv6 address"),
        protocol="IPv6",
        help_text=_("The IPv6 address of the network."),
    )

    subnet_mask_v4 = models.PositiveIntegerField(
        verbose_name=_("IPv4 subnet mask"),
        default=24,
        validators=[validators.MinValueValidator(1), validators.MaxValueValidator(31)],
        help_text=_("The IPv4 subnet mask of the network."),
    )

    subnet_mask_v6 = models.PositiveIntegerField(
        verbose_name=_("IPv6 subnet mask"),
        default=64,
        validators=[validators.MinValueValidator(1), validators.MaxValueValidator(127)],
        help_text=_("The IPv6 subnet mask of the network."),
    )

    enable_v4 = models.BooleanField(
        verbose_name=_("Enable IPv4 addresses"),
        default=True,
        help_text=_("If IPv4 addresses should be enabled for the network."),
    )
    enable_v6 = models.BooleanField(
        verbose_name=_("Enable IPv6 addresses"),
        default=True,
        help_text=_("If IPv6 addresses should be enabled for the network."),
    )

    dynamic_range_v4_start = models.GenericIPAddressField(
        protocol="IPv4", help_text=_("The start of the range.")
    )
    dynamic_range_v4_end = models.GenericIPAddressField(
        protocol="IPv4", help_text=_("The end of the range.")
    )

    dynamic_range_v6_start = models.GenericIPAddressField(
        protocol="IPv6", help_text=_("The start of the range.")
    )
    dynamic_range_v6_end = models.GenericIPAddressField(
        protocol="IPv6", help_text=_("The end of the range.")
    )

    machine_set: models.Manager["Machine"]

    objects = Manager()

    def natural_key(self) -> Tuple[str]:
        return (self.name,)

    def __str__(self) -> str:
        return self.name

    def clean(self):
        if not self.enable_v4 and not self.enable_v6:
            raise ValidationError(
                _("Must have at least one of IPv4 and/or IPv6 enabled")
            )

    def save(self, *args: Any, **kwargs: Any) -> None:
        validate_domain_ending(self.name)

        super(Domain, self).save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> Tuple[int, Dict[str, int]]:
        if self.machine_set.count() > 0:
            raise ValidationError("Domain contains machines.")
        else:
            return super(Domain, self).delete(*args, **kwargs)

    @admin.display(description="Machines")
    def get_machine_count(self) -> int:
        return self.machine_set.count()

    def get_setup_records(
        self, architecture: str, delimiter: str = ":"
    ) -> Union[List[str], Dict[str, List[str]]]:
        """
        Collect domain and architecture or machine group specific setup records.

        Each domain has one optional TFTP server providing available records for machine setup.

        :returns: The list of setup records from the TFTP server.
        """

        if not self.tftp_server:
            logger.warning("No TFTP server available for '%s'", self.name)
            return {}

        server = CobblerServer(self.tftp_server.fqdn_domain)
        records = server.get_profiles(architecture)
        logger.debug("Records:\n%s", records)
        delim_c = records[0].count(delimiter)
        if delim_c == 1:
            # <distro>:<profile>
            pass
        elif delim_c == 2:
            # <arch>:<distro>:<profile>
            records = [record.split(delimiter, maxsplit=1)[1] for record in records]
        logger.debug("Not grouped and parsed:\n%s", records)

        return records

    def get_setup_records_grouped(
        self, architecture: str, delimiter: str = ":"
    ) -> Dict[str, List[str]]:
        """
        Collect domain and architecture or machine group specific setup records.

        Each domain has one optional TFTP server providing available records for machine setup.

        :returns: The list of setup records from the TFTP server grouped. They key is the distribution and the value is
                  a list of profile suffixes.
        """
        server = CobblerServer(self.tftp_server.fqdn_domain)  # type: ignore
        profiles = server.get_profiles(architecture)

        groups: Dict[str, List[str]] = {}
        for record in profiles:
            delim_c = record.count(delimiter)
            # <distro>:<profile>
            if delim_c == 1:
                (distro, profile) = record.split(delimiter)
            # <arch>:<distro>:<profile>
            elif delim_c == 2:
                (_arch, distro, profile) = record.split(delimiter)
            else:
                logger.debug("Setup record has invalid format: '%s'", record)
                continue

            if distro not in groups:
                groups[distro] = []

            groups[distro].append(profile)
        records = collections.OrderedDict(sorted(groups.items()))
        logger.debug("Grouped and parsed:\n%s", records)

        return records

    def is_valid_setup_choice(self, choice: str, architecture: str) -> bool:
        """Check if `choice` is a valid setup record."""
        choices = self.get_setup_records(architecture)
        result = choice in choices
        logger.debug('Is valid setup choice? - "%s"', result)
        return result


class DomainAdmin(models.Model):

    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, blank=False)
    arch = models.ForeignKey(Architecture, on_delete=models.CASCADE, blank=False)

    contact_email = models.EmailField(blank=False)

    def natural_key(self) -> Tuple[str, str]:
        return self.domain.name, self.arch.name
