import logging

from django.db import models

logger = logging.getLogger('models')


class Component(models.Model):

    class Meta:
        abstract = True

    machine = models.ForeignKey(
        'data.Machine',
        on_delete=models.CASCADE,
        null=False
    )
