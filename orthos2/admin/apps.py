from django.contrib.admin.apps import AdminConfig


class OrthosAdminConfig(AdminConfig):
    default_site = "orthos2.admin.site.MyAdminSite"
