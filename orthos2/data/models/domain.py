import collections
import logging
from typing import Dict, List, Union

from django.core.exceptions import ValidationError
from django.db import models

from orthos2.data.models.architecture import Architecture
from orthos2.data.models.serverconfig import ServerConfig
from orthos2.utils.cobbler import CobblerServer
from orthos2.utils.misc import has_valid_domain_ending

logger = logging.getLogger("models")


def validate_domain_ending(value):
    valid_domain_endings = ServerConfig.objects.get_valid_domain_endings()

    if not has_valid_domain_ending(value, valid_domain_endings):
        raise ValidationError(
            "'{}' has no valid domain ending ({}).".format(
                value, ", ".join(valid_domain_endings)
            )
        )


class Domain(models.Model):
    class Manager(models.Manager):
        def get_by_natural_key(self, name):
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

    supported_architectures = models.ManyToManyField(
        "data.Architecture",
        related_name="supported_domains",
        verbose_name="Supported architectures",
        through="DomainAdmin",
        blank=False,
    )

    objects = Manager()

    def natural_key(self):
        return (self.name,)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        validate_domain_ending(self.name)

        super(Domain, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.machine_set.count() > 0:
            raise ValidationError("Domain contains machines.")
        else:
            super(Domain, self).delete(*args, **kwargs)

    def get_machine_count(self):
        return self.machine_set.count()

    get_machine_count.short_description = "Machines"

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
        server = CobblerServer(self.tftp_server.fqdn_domain)
        profiles = server.get_profiles(architecture)

        groups = {}
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

    def is_valid_setup_choice(self, choice: str, architecture: str):
        """Check if `choice` is a valid setup record."""
        choices = self.get_setup_records(architecture)
        result = choice in choices
        logger.debug('Is valid setup choice? - "%s"', result)
        return result


class DomainAdmin(models.Model):

    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, blank=False)
    arch = models.ForeignKey(Architecture, on_delete=models.CASCADE, blank=False)

    contact_email = models.EmailField(blank=False)

    def natural_key(self):
        return self.domain.name, self.arch.name
