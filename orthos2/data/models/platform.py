from django.db import models

from .vendor import Vendor


class Platform(models.Model):

    class Meta:
        ordering = ['vendor', 'name']

    name = models.CharField(
        max_length=200,
        blank=False
    )

    vendor = models.ForeignKey(
        Vendor,
        blank=False,
        null=False,
        on_delete=models.CASCADE
    )

    is_cartridge = models.BooleanField(
        'Cartridge/Blade',
        default=False
    )

    description = models.CharField(
        max_length=512,
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

    def __str__(self):
        return self.name

    def get_vendor(self):
        return self.vendor.name
    get_vendor.short_description = 'Vendor'

    def get_enclosure_count(self):
        return self.enclosure_set.count()
    get_enclosure_count.short_description = 'Enclosures'
