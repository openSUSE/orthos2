from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from orthos2.utils.misc import safe_get_or_default


class System(models.Model):

    class Type:

        @classmethod
        def prep(cls):
            """Preparation of const variables for fast and developer-friendly handling."""
            cls.BAREMETAL = safe_get_or_default(
                System,
                'name',
                'BareMetal',
                'pk',
                -1
            )

    help_text="Describes the system type of a machine"

    name = models.CharField(
        max_length=200,
        blank=False,
        unique=True,
        help_text="What kind of system are these machines?"
    )

    virtual = models.BooleanField(
        default=False,
        null=False,
        blank=False,
        help_text="Are these machines virtual systems (can have a hypervisor)?"
    )

    allowBMC = models.BooleanField(
        default=False,
        null=False,
        blank=False,
        help_text="Can a network interface be assigned to such a system serving as BMC?"
    )

    allowHypervisor = models.BooleanField(
        default=False,
        null=False,
        blank=False,
        help_text="Can such systems host virtual machines?"
    )

    administrative = models.BooleanField(
        default=False,
        null=False,
        blank=False,
        help_text="Are these machines administrative systems (cannot be installed or reserved)?"
    )

    created = models.DateTimeField('created at', auto_now=True)

    def __str__(self):
        return self.name
