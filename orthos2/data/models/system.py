from django.core.exceptions import ObjectDoesNotExist
from django.db import models


class System(models.Model):

    class Type:
        BAREMETAL = 0
        BLADESERVER = 1
        KVM_VM = 20
        PKVM_VM = 21
        XEN_VM = 22
        ZVM_VM = 23
        ZVM_KVM = 24
        LPAR_POWERPC = 30
        LPAR_ZSERIES = 31
        DESKTOP = 40
        REMOTEPOWER = 90
        BMC = 91

    name = models.CharField(
        max_length=200,
        blank=False,
        unique=True
    )

    virtual = models.BooleanField(
        default=False,
        null=False,
        blank=False
    )

    administrative = models.BooleanField(
        default=False,
        null=False,
        blank=False
    )

    created = models.DateTimeField('created at', auto_now=True)

    def __str__(self):
        return self.name
