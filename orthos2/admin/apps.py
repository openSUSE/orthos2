from django.contrib.admin.apps import AdminConfig

class AdminConfig(AdminConfig):
    default_site = 'orthos2.admin.site.MyAdminSite'
