from copy import deepcopy

from django.db import models

from orthos2.utils.misc import safe_get_or_default


class Architecture(models.Model):

    class Manager(models.Manager):
        def get_by_natural_key(self, name):
            return self.get(name=name)

    class Type:

        @classmethod
        def prep(cls):
            """Prepare const variables for fast and developer-friendly handling."""
            cls.X86_64 = safe_get_or_default(
                Architecture,
                'name',
                'x86_64',
                'pk',
                -1
            )
            cls.PPC64LE = safe_get_or_default(
                Architecture,
                'name',
                'ppc64le',
                'pk',
                -1
            )

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

    objects = Manager()

    def natural_key(self):
        return (self.name,)

    def __init__(self, *args, **kwargs):
        """Deep copy object for comparison in `save()`."""
        super(Architecture, self).__init__(*args, **kwargs)

        if self.pk is not None:
            self._original = deepcopy(self)
        else:
            self._original = None

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Save architecture object."""
        super(Architecture, self).save(*args, **kwargs)

        # check if DHCP needs to be regenerated
        if self._original is not None:
            try:
                assert self.dhcp_filename == self._original.dhcp_filename
            except AssertionError:
                from orthos2.data.signals import signal_dhcp_regenerate

                signal_dhcp_regenerate.send(sender=self.__class__, domain_id=None)

    def get_machine_count(self):
        return self.machine_set.count()
    get_machine_count.short_description = 'Machines'

    def get_support_contact(self):
        """Return email address for responsible support contact."""
        if self.contact_email:
            return self.contact_email

        return None
