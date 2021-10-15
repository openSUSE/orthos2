from django.db import models


class Vendor(models.Model):

    class Meta:
        ordering = ['name']

    name = models.CharField(
        max_length=100,
        blank=False,
        unique=True
    )

    def natural_key(self):
        return self.name

    def __str__(self):
        return self.name
