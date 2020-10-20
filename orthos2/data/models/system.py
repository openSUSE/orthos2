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
            cls.REMOTEPOWER = safe_get_or_default(
                System,
                'name',
                'RemotePower',
                'pk',
                -1
            )
            cls.BMC = safe_get_or_default(
                System,
                'name',
                'BMC',
                'pk',
                -1
            )

    name = models.CharField(
        max_length=200,
        blank=False,
        unique=True
    )

    virtual = models.BooleanField(
        default=False,
        null=False,
        blank=False
    )

    administrative = models.BooleanField(
        default=False,
        null=False,
        blank=False
    )

    created = models.DateTimeField('created at', auto_now=True)

    def __str__(self):
        return self.name
