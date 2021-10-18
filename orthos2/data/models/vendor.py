from django.db import models


class Vendor(models.Model):

    class Manager(models.Manager):
        def get_by_natural_key(self, name):
            return self.get(name=name)

    class Meta:
        ordering = ['name']

    name = models.CharField(
        max_length=100,
        blank=False,
        unique=True
    )

    objects = Manager()

    def natural_key(self):
        return (self.name,)

    def __str__(self):
        return self.name
