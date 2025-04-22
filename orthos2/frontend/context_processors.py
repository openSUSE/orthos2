from orthos2 import settings


def netbox_url(request):
    return {"NETBOX_URL": settings.NETBOX_URL}
