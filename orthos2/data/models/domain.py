import collections
import logging

from django.core.exceptions import ValidationError
from django.db import models
from django.template import Context, Template

from .architecture import Architecture
from .serverconfig import ServerConfig

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

    def get_setup_records(self, architecture, grouped=True, delimiter=":"):
        """
        Collect domain and architecture or machine group specific setup records.

        Each domain has one optional TFTP server providing available records for machine setup.

        If `grouped` is False, a list of all records gets returned (no grouping).

        Expects as return value when executing 'setup.list.command' below:

            ['<architecture|machinegroup:>DISTRIBUTION:FLAVOUR', ...]

        e.g.:

            [
                'x86_64:SLES12-SP3:install\n',
                'x86_64:SLES12-SP3:install-ssh\n',
                ...
                'x86_64:SLES12-SP2:install\n',
                'x86_64:SLES12-SP2:rescue\n',
                ...,
                'x86_64:local\n',
                ...,
            ]


        Returns (grouped is `True`):

            OrderedDict([
                ('SLES12-SP3', [
                    'install',
                    'install-ssh',
                    ...
                ]),
                ('SLES12-SP2', [
                    'install',
                    'rescue',
                    ...
                ]),
                ('local', [
                    ''
                ])
            )


        Returns (grouped is `False`):

            [
                'SLES12-SP3:install',
                'SLES12-SP3:install-ssh',
                ...
                'SLES12-SP2:install',
                'SLES12-SP2:rescue',
                ...,
                'local',
                ...,
            ]
        """
        from orthos2.utils.ssh import SSH

        if not self.tftp_server:
            logger.warning("No TFTP server available for '%s'", self.name)
            return {}

        list_command_template = ServerConfig.objects.by_key("setup.list.command")

        context = Context({"architecture": architecture})
        list_command = Template(list_command_template).render(context)

        try:
            conn = SSH(self.tftp_server.fqdn)
            conn.connect()
            logger.debug(
                "Fetch setup records: %s:%s", self.tftp_server.fqdn, list_command
            )
            stdout, stderr, exitstatus = conn.execute(list_command)
            conn.close()

            if exitstatus != 0:
                logger.warning(str(stderr))
                return {}

            logger.debug(
                "Found %s setup records on %s", len(stdout), self.tftp_server.fqdn
            )
        except Exception as e:
            logger.warning("Couldn't fetch record list for setup: %s", str(e))
            return {}
        finally:
            if conn:
                conn.close()

        records = [record.strip("\n") for record in stdout]
        logger.debug("Records:\n%s", records)
        if grouped:
            groups = {}
            for record in records:
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
        else:
            delim_c = records[0].count(delimiter)
            if delim_c == 1:
                # <distro>:<profile>
                pass
            elif delim_c == 2:
                # <arch>:<distro>:<profile>
                records = [record.split(delimiter, maxsplit=1)[1] for record in records]
            logger.debug("Not grouped and parsed:\n%s", records)

        return records

    def is_valid_setup_choice(self, choice, architecture):
        """Check if `choice` is a valid setup record."""
        choices = self.get_setup_records(architecture, grouped=False)
        result = choice in choices
        logger.debug(result)
        return result


class DomainAdmin(models.Model):

    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, blank=False)
    arch = models.ForeignKey(Architecture, on_delete=models.CASCADE, blank=False)

    contact_email = models.EmailField(blank=False)

    def natural_key(self):
        return (self.domain.name, self.arch.name)
