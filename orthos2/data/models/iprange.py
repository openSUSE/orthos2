from django.db import models


class IPRangeV4(models.Model):
    start = models.GenericIPAddressField(protocol="IPv4")
    end = models.GenericIPAddressField(protocol="IPv4")


class IPRangeV6(models.Model):
    start = models.GenericIPAddressField(protocol="IPv6")
    end = models.GenericIPAddressField(protocol="IPv6")
