from django.conf.urls import include, url
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView

from . import ajax, views
app_name = 'frontend'
urlpatterns = [
    url(r'^$', RedirectView.as_view(pattern_name='frontend:free_machines'), name='root'),
    url(r'^machines$', RedirectView.as_view(pattern_name='frontend:free_machines'),
        name='free_machines'),
    url(r'^machines/all$', views.AllMachineListView.as_view(), name='machines'),
    url(r'^machines/free$', views.FreeMachineListView.as_view(), name='free_machines'),
    url(r'^machines/my$', views.MyMachineListView.as_view(), name='my_machines'),
    url(
        r'^machines/virtualmachines$',
        views.VirtualMachineListView.as_view(),
        name='virtual_machines'
    ),
    url(r'^machines/search', views.machine_search, name='advanced_search'),
    url(r'^machine/(?P<id>[0-9]+)/$', views.machine, name='detail'),
    url(r'^machine/(?P<id>[0-9]+)/detail$', views.machine, name='detail'),
    url(r'^machine/(?P<id>[0-9]+)/cpu$', views.cpu, name='cpu'),
    url(
        r'^machine/(?P<id>[0-9]+)/networkinterfaces$',
        views.networkinterfaces,
        name='networkinterfaces'
    ),
    url(r'^machine/(?P<id>[0-9]+)/pci$', views.pci, name='pci'),
    url(r'^machine/(?P<id>[0-9]+)/installations$', views.installations, name='installations'),
    url(r'^machine/(?P<id>[0-9]+)/usb$', views.usb, name='usb'),
    url(r'^machine/(?P<id>[0-9]+)/scsi$', views.scsi, name='scsi'),
    url(r'^machine/(?P<id>[0-9]+)/miscellaneous$', views.misc, name='misc'),
    url(r'^machine/(?P<id>[0-9]+)/history$', views.history, name='history'),
    url(r'^machine/(?P<id>[0-9]+)/reserve$', views.machine_reserve, name='reserve_machine'),
    url(r'^machine/(?P<id>[0-9]+)/release$', views.machine_release, name='release_machine'),
    url(r'^machine/(?P<id>[0-9]+)/rescan$', views.rescan, name='rescan'),
    url(r'^machine/(?P<id>[0-9]+)/setup$', views.setup, name='setup'),
    url(r'^machine/(?P<id>[0-9]+)/virtualization$', views.virtualization, name='virtualization'),
    url(
        r'^machine/(?P<id>[0-9]+)/virtualization/add$',
        views.virtualization_add,
        name='virtualization_add'
    ),
    url(r'^machine/(?P<id>[0-9]+)/console$', views.console, name='console'),
    url(r'^login/$', views.login, name='login'),
    url(r'^logout/$', auth_views.LogoutView.as_view(), {'next_page': '/'}, name='logout'),
    url(r'^user/create$', views.users_create, name='create_user'),
    url(r'^user/preferences$', views.users_preferences, name='preferences_user'),
    url(r'^password/restore$', views.users_password_restore, name='password_restore'),
    url(r'^statistics$', views.statistics, name='statistics'),
    url(
        r'^ajax/machine/(?P<machine_id>[0-9]+)/annotation/add',
        ajax.annotation,
        name='ajax_annotation'
    ),
    url(
        r'^ajax/machine/(?P<machine_id>[0-9]+)/powercycle$',
        ajax.powercycle,
        name='ajax_powercycle'
    ),
    url(
        r'^ajax/machine/(?P<host_id>[0-9]+)/virtualization/list$',
        ajax.virtualization_list,
        name='ajax_virtualization_list'
    ),
    url(
        r'^ajax/machine/(?P<host_id>[0-9]+)/virtualization/delete$',
        ajax.virtualization_delete,
        name='ajax_virtualization_delete'
    ),
]
