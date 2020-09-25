import collections
import logging
import re

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import models
from django.template import Context, Template
from django.utils.translation import ugettext_lazy as _

from utils.misc import has_valid_domain_ending

from .architecture import Architecture
from .machinegroup import MachineGroup
from .serverconfig import ServerConfig

logger = logging.getLogger('models')


def validate_domain_ending(value):
    valid_domain_endings = ServerConfig.objects.get_valid_domain_endings()

    if not has_valid_domain_ending(value, valid_domain_endings):
        raise ValidationError(_("'{}' has no valid domain ending ({}).".format(
            value,
            ', '.join(valid_domain_endings)
        )))


class Domain(models.Model):
    name = models.CharField(
        max_length=200,
        blank=False,
        unique=True,
        validators=[validate_domain_ending]
    )

    cobbler_server = models.ManyToManyField(
        'data.Machine',
        related_name='cobbler_server_for',
        verbose_name='Cobbler server',
        blank=True,
        limit_choices_to={'administrative': True}
    )

    tftp_server = models.ForeignKey(
        'data.Machine',
        related_name='tftp_server_for',
        verbose_name='TFTP server',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        limit_choices_to={'administrative': True}
    )

    setup_architectures = models.ManyToManyField(
        'data.Architecture',
        related_name='setup_domains',
        verbose_name='Setup architectures',
        blank=True
    )

    setup_machinegroups = models.ManyToManyField(
        'data.MachineGroup',
        related_name='setup_domains',
        verbose_name='Setup machine groups',
        blank=True
    )

    updated = models.DateTimeField(
        'Updated at',
        auto_now=True
    )

    created = models.DateTimeField(
        'Created at',
        auto_now_add=True
    )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        validate_domain_ending(self.name)

        super(Domain, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.machine_set.count() > 0:
            raise ValidationError(_("Domain contains machines."))
        else:
            super(Domain, self).delete(*args, **kwargs)

    def get_machine_count(self):
        return self.machine_set.count()
    get_machine_count.short_description = 'Machines'

    def get_setup_records(self, architecture, machinegroup=None, grouped=True, delimiter=':'):
        """
        Collect domain and architecture or machine group specific setup records.
 
        Each domain has one optional TFTP server providing available records for machine setup.

        If `grouped` is False, a list of all records gets returned (no grouping).

        Expects stdout:

            ['DISTRIBUTION-<architecture|machinegroup>-FLAVOUR', ...]

            [
                'SLES12-SP3-x86_64-install\n',
                'SLES12-SP3-x86_64-install-ssh\n',
                ...
                'SLES12-SP2-x86_64-install\n',
                'SLES12-SP2-x86_64-rescue\n',
                ...,
                'local-x86_64\n',
                ...,
            ]


        Returns (grouped is `True`):

            OrderedDict([
                ('SLES12-SP3', [
                    'SLES12-SP3-x86_64-install',
                    'SLES12-SP3-x86_64-install-ssh',
                    ...
                ]),
                ('SLES12-SP2', [
                    'SLES12-SP2-x86_64-install',
                    'SLES12-SP2-x86_64-rescue',
                    ...
                ]),
                ('local', [
                    'local-x86_64'
                ])
            )


        Returns (grouped is `False`):

            [
                'SLES12-SP3-x86_64-install',
                'SLES12-SP3-x86_64-install-ssh',
                ...
                'SLES12-SP2-x86_64-install',
                'SLES12-SP2-x86_64-rescue',
                ...,
                'local-x86_64',
                ...,
            ]
        """
        from utils.ssh import SSH

        def grouping(records):
            """Group records for HTML form."""
            groups = {}

            for record in records:
                record_ = record.split(delimiter)

                if len(record_) == 2:
                    prefix = record_[0]
                    suffix = record_[1]
                else:
                    logger.debug("Setup record has invalid format: '{}'".format(record))
                    continue

                if prefix not in groups:
                    groups[prefix] = []

                groups[prefix].append(suffix)

            return collections.OrderedDict(sorted(groups.items()))
        if not self.tftp_server:
            logger.warning("No TFTP server available for '{}'".format(self.name))
            return {}

        list_command_template = ServerConfig.objects.by_key('setup.list.command')

        context = Context({
            'architecture': architecture,
            'machinegroup': machinegroup
        })
        list_command = Template(list_command_template).render(context)

        try:
            conn = SSH(self.tftp_server.fqdn)
            conn.connect()
            logger.debug("Fetch setup records: {}:{}".format(self.tftp_server.fqdn, list_command))
            stdout, stderr, exitstatus = conn.execute(list_command)
            conn.close()

            if exitstatus != 0:
                logger.warning(str(stderr))
                return {}

            logger.debug("Found {} setup records on {}".format(len(stdout), self.tftp_server.fqdn))

        except Exception as e:
            logger.warning("Couldn't fetch record list for setup: {}".format(str(e)))
            return {}
        finally:
            if conn:
                conn.close()

        records = list(map(lambda record: record.strip('\n'), stdout))
        if grouped:
            records = grouping(records)
        else:
            records = list(map(lambda record: record.split(delimiter)[1], records))

        return records

    def is_valid_setup_choice(self, choice, architecture, machinegroup=None):
        """Check if `choice` is a valid setup record."""
        choices = self.get_setup_records(
            architecture,
            machinegroup=machinegroup,
            grouped=False
        )
        return choice in choices
