from django.conf import settings as django_settings
from django.http import HttpRequest

from orthos2 import settings


def netbox_url(request: HttpRequest):
    return {"NETBOX_URL": settings.NETBOX_URL}


def grafana_url(request: HttpRequest):
    # Uses django.conf.settings (rather than `from orthos2 import settings`, like
    # netbox_url above) so that @override_settings works as expected in tests.
    return {
        "GRAFANA_URL": django_settings.GRAFANA_URL,
        "GRAFANA_HOST_DASHBOARD_UID": django_settings.GRAFANA_HOST_DASHBOARD_UID,
    }
