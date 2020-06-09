from django.contrib.auth.models import User
from django.db import models


class Annotation(models.Model):

    class Meta:
        ordering = ['-created']

    machine = models.ForeignKey(
        'data.Machine',
        related_name='annotations',
        editable=False,
        on_delete=models.CASCADE
    )

    text = models.CharField(
        max_length=1024,
        blank=False
    )

    reporter = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
        editable=False
    )

    created = models.DateTimeField(
        'Created at',
        auto_now_add=True
    )

    def __str__(self):
        return self.machine.fqdn
