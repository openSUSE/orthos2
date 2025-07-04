from django.http import HttpRequest

from orthos2 import settings


def netbox_url(request: HttpRequest):
    return {"NETBOX_URL": settings.NETBOX_URL}
