from django.db import models
from django.core import validators
from orthos2.data.validators import DomainNameValidator
from orthos2.data.models.iprange import IPRangeV4, IPRangeV6
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class Network(models.Model):
    class Meta:
        verbose_name = "Network"
        ordering = ("-name",)

    name = models.CharField(
        max_length=256,
        blank=False,
        default="unknown",
        validators=[DomainNameValidator()],
    )

    ip_v4 = models.GenericIPAddressField(
        protocol="IPv4",
    )

    ip_v6 = models.GenericIPAddressField(
        protocol="IPv6",
    )

    subnet_mask_v4 = models.PositiveIntegerField(
        default=24,
        validators=[validators.MinValueValidator(1), validators.MaxValueValidator(31)],
    )

    subnet_mask_v6 = models.PositiveIntegerField(
        default=64,
        validators=[validators.MinValueValidator(1), validators.MaxValueValidator(127)],
    )

    enable_v4 = models.BooleanField(default=True)
    enable_v6 = models.BooleanField(default=True)

    dynamic_range_v4 = models.OneToOneField[IPRangeV4, IPRangeV4](
        IPRangeV4, on_delete=models.CASCADE
    )

    dynamic_range_v6 = models.OneToOneField(IPRangeV6, on_delete=models.CASCADE)

    def clean(self):
        if not self.enable_v4 and not self.enable_v6:
            raise ValidationError(
                _("Must have at least one of IPv4 and/or IPv6 enabled")
            )
