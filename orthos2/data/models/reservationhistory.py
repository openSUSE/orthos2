from django.db import models

from .machine import Machine


class ReservationHistory(models.Model):

    class Meta:
        ordering = ['-created']

    machine = models.ForeignKey(
        Machine,
        editable=False,
        on_delete=models.CASCADE
    )

    reserved_by = models.CharField(
        max_length=200,
        blank=False,
        null=False,
    )

    reserved_at = models.DateTimeField(
        blank=False,
        null=False
    )

    reserved_until = models.DateTimeField(
        blank=False,
        null=False
    )

    reserved_reason = models.CharField(
        'Reservation reason',
        max_length=512,
        blank=False,
        null=False
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
        return "{} ({})".format(self.reserved_by, self.machine.fqdn)
