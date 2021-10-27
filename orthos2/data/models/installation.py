from django.db import models

from .machine import Machine


class Installation(models.Model):
    machine = models.ForeignKey(
        Machine,
        related_name='installations',
        editable=False,
        on_delete=models.CASCADE
    )

    active = models.BooleanField(
        blank=False,
        default=True
    )

    architecture = models.CharField(
        max_length=200,
        blank=True
    )

    distribution = models.CharField(
        max_length=200,
        blank=True
    )

    kernelversion = models.CharField(
        'Kernel version',
        max_length=100,
        blank=True
    )

    partition = models.CharField(
        max_length=100,
        blank=True
    )

    def __str__(self):
        if self.active:
            return "{} ({})".format(self.distribution, 'active')
        return self.distribution
