from django.urls import re_path
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView

from . import ajax, views
app_name = 'orthos2.frontend'
urlpatterns = [
    re_path(r'^$', RedirectView.as_view(pattern_name='frontend:free_machines'), name='root'),
    re_path(
        r'^machines$',
        RedirectView.as_view(pattern_name='frontend:free_machines'),
        name='free_machines'
    ),
    re_path(r'^machines/all$', views.AllMachineListView.as_view(), name='machines'),
    re_path(r'^machines/free$', views.FreeMachineListView.as_view(), name='free_machines'),
    re_path(r'^machines/my$', views.MyMachineListView.as_view(), name='my_machines'),
    re_path(
        r'^machines/virtualmachines$',
        views.VirtualMachineListView.as_view(),
        name='virtual_machines'
    ),
    re_path(r'^machines/search', views.machine_search, name='advanced_search'),
    re_path(r'^machine/(?P<id>[0-9]+)/$', views.machine, name='detail'),
    re_path(r'^machine/(?P<id>[0-9]+)/detail$', views.machine, name='detail'),
    re_path(r'^machine/(?P<id>[0-9]+)/cpu$', views.cpu, name='cpu'),
    re_path(
        r'^machine/(?P<id>[0-9]+)/networkinterfaces$',
        views.networkinterfaces,
        name='networkinterfaces'
    ),
    re_path(r'^machine/(?P<id>[0-9]+)/pci$', views.pci, name='pci'),
    re_path(r'^machine/(?P<id>[0-9]+)/installations$', views.installations, name='installations'),
    re_path(r'^machine/(?P<id>[0-9]+)/usb$', views.usb, name='usb'),
    re_path(r'^machine/(?P<id>[0-9]+)/scsi$', views.scsi, name='scsi'),
    re_path(r'^machine/(?P<id>[0-9]+)/miscellaneous$', views.misc, name='misc'),
    re_path(r'^machine/(?P<id>[0-9]+)/history$', views.history, name='history'),
    re_path(r'^machine/(?P<id>[0-9]+)/reserve$', views.machine_reserve, name='reserve_machine'),
    re_path(r'^machine/(?P<id>[0-9]+)/release$', views.machine_release, name='release_machine'),
    re_path(r'^machine/(?P<id>[0-9]+)/rescan$', views.rescan, name='rescan'),
    re_path(r'^machine/(?P<id>[0-9]+)/setup$', views.setup, name='setup'),
    re_path(
        r'^machine/(?P<id>[0-9]+)/virtualization$',
        views.virtualization,
        name='virtualization'
    ),
    re_path(
        r'^machine/(?P<id>[0-9]+)/virtualization/add$',
        views.virtualization_add,
        name='virtualization_add'
    ),
    re_path(r'^machine/(?P<id>[0-9]+)/console$', views.console, name='console'),
    re_path(r'^login/$', views.login, name='login'),
    re_path(r'^logout/$', auth_views.LogoutView.as_view(), {'next_page': '/'}, name='logout'),
    re_path(r'^user/create$', views.users_create, name='create_user'),
    re_path(r'^user/preferences$', views.users_preferences, name='preferences_user'),
    re_path(r'^password/restore$', views.users_password_restore, name='password_restore'),
    re_path(r'^statistics$', views.statistics, name='statistics'),
    re_path(
        r'^ajax/machine/(?P<machine_id>[0-9]+)/annotation/add',
        ajax.annotation,
        name='ajax_annotation'
    ),
    re_path(
        r'^ajax/machine/(?P<machine_id>[0-9]+)/powercycle$',
        ajax.powercycle,
        name='ajax_powercycle'
    ),
    re_path(
        r'^ajax/machine/(?P<host_id>[0-9]+)/virtualization/list$',
        ajax.virtualization_list,
        name='ajax_virtualization_list'
    ),
    re_path(
        r'^ajax/machine/(?P<host_id>[0-9]+)/virtualization/delete$',
        ajax.virtualization_delete,
        name='ajax_virtualization_delete'
    ),
]
