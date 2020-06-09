from django.db import models


class Vendor(models.Model):

    class Meta:
        ordering = ['name']

    name = models.CharField(
        max_length=100,
        blank=False,
        unique=True
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
