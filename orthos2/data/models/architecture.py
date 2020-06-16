from copy import deepcopy

from django.db import models


class Architecture(models.Model):

    class Type:
        X86_64 = 0
        PPC = 10
        PPC64 = 11
        PPC64LE = 12
        ARMV7 = 20
        AARCH64 = 21
        S390X = 30
        IA64 = 40
        EMBEDDED = 99
        UNSPECIFIED = 100

    name = models.CharField(
        max_length=200,
        blank=False,
        unique=True
    )

    dhcp_filename = models.CharField(
        'DHCP filename',
        max_length=64,
        null=True,
        blank=True
    )

    contact_email = models.EmailField(
        blank=True
    )

    dhcpv4_write = models.BooleanField(
        'Write DHCPv4',
        default=True
    )

    dhcpv6_write = models.BooleanField(
        'Write DHCPv6',
        default=True
    )

    updated = models.DateTimeField(
        'Updated at',
        auto_now=True
    )

    created = models.DateTimeField(
        'Created at',
        auto_now_add=True
    )
    default_profile = models.CharField(
        'Default profile',
        max_length=128,
        null=True,
        blank=True
    )

    def __init__(self, *args, **kwargs):
        """
        Deep copy object for comparison in `save()`.
        """
        super(Architecture, self).__init__(*args, **kwargs)

        if self.pk is not None:
            self._original = deepcopy(self)
        else:
            self._original = None

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """
        Save architecture object.
        """
        super(Architecture, self).save(*args, **kwargs)

        # check if DHCP needs to be regenerated
        if self._original is not None:
            try:
                assert self.dhcp_filename == self._original.dhcp_filename
                assert self.dhcpv4_write == self._original.dhcpv4_write
                assert self.dhcpv6_write == self._original.dhcpv6_write
            except AssertionError:
                from data.signals import signal_dhcp_regenerate

                signal_dhcp_regenerate.send(sender=self.__class__, domain_id=None)

    def get_machine_count(self):
        return self.machine_set.count()
    get_machine_count.short_description = 'Machines'

    def get_support_contact(self):
        """
        Returns email address for responsible support contact.
        """
        if self.contact_email:
            return self.contact_email

        return None
