from django.core import validators
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext as _

from orthos2.data.validators import DomainNameValidator


class Network(models.Model):
    class Meta:
        verbose_name = "Network"
        ordering = ("-name",)

    name = models.CharField(
        max_length=256,
        blank=False,
        default="unknown",
        validators=[DomainNameValidator()],
        help_text=_(
            "The name of the network. Should at least relate to an existing Domain object."
        ),
    )

    ip_v4 = models.GenericIPAddressField(
        verbose_name=_("IPv4 address"),
        protocol="IPv4",
        help_text=_("The IPv4 address of the network."),
    )

    ip_v6 = models.GenericIPAddressField(
        verbose_name=_("IPv6 address"),
        protocol="IPv6",
        help_text=_("The IPv6 address of the network."),
    )

    subnet_mask_v4 = models.PositiveIntegerField(
        verbose_name=_("IPv4 subnet mask"),
        default=24,
        validators=[validators.MinValueValidator(1), validators.MaxValueValidator(31)],
        help_text=_("The IPv4 subnet mask of the network."),
    )

    subnet_mask_v6 = models.PositiveIntegerField(
        verbose_name=_("IPv6 subnet mask"),
        default=64,
        validators=[validators.MinValueValidator(1), validators.MaxValueValidator(127)],
        help_text=_("The IPv6 subnet mask of the network."),
    )

    enable_v4 = models.BooleanField(
        verbose_name=_("Enable IPv4 addresses"),
        default=True,
        help_text=_("If IPv4 addresses should be enabled for the network."),
    )
    enable_v6 = models.BooleanField(
        verbose_name=_("Enable IPv6 addresses"),
        default=True,
        help_text=_("If IPv6 addresses should be enabled for the network."),
    )

    dynamic_range_v4_start = models.GenericIPAddressField(
        protocol="IPv4", help_text=_("The start of the range.")
    )
    dynamic_range_v4_end = models.GenericIPAddressField(
        protocol="IPv4", help_text=_("The end of the range.")
    )

    dynamic_range_v6_start = models.GenericIPAddressField(
        protocol="IPv6", help_text=_("The start of the range.")
    )
    dynamic_range_v6_end = models.GenericIPAddressField(
        protocol="IPv6", help_text=_("The end of the range.")
    )

    def clean(self):
        if not self.enable_v4 and not self.enable_v6:
            raise ValidationError(
                _("Must have at least one of IPv4 and/or IPv6 enabled")
            )
