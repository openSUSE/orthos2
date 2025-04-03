from django.db import models
from django.utils.translation import gettext as _


class IPRangeV4(models.Model):
    class Meta:
        verbose_name = "IP Range V4"

    start = models.GenericIPAddressField(
        protocol="IPv4", help_text=_("The start of the range.")
    )
    end = models.GenericIPAddressField(
        protocol="IPv4", help_text=_("The end of the range.")
    )


class IPRangeV6(models.Model):
    class Meta:
        verbose_name = "IP Range V6"

    start = models.GenericIPAddressField(
        protocol="IPv6", help_text=_("The start of the range.")
    )
    end = models.GenericIPAddressField(
        protocol="IPv6", help_text=_("The end of the range.")
    )
