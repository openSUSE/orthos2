from django.contrib.auth import views as auth_views
from django.urls import path, re_path
from django.views.generic import RedirectView

from orthos2.frontend import views

app_name = "orthos2.frontend"
urlpatterns = [
    path("enclosures", views.EnclosureListView.as_view(), name="enclosures"),
    re_path(
        r"^enclosure/(?P<id>[0-9]+)/detail$",
        views.enclosure_detail,
        name="enclosure_detail",
    ),
    re_path(
        r"^enclosure/(?P<id>[0-9]+)/machines$",
        views.enclosure_machines,
        name="enclosure_machines",
    ),
    re_path(
        r"^enclosure/(?P<id>[0-9]+)/netboxcomparison$",
        views.enclosure_netboxcomparison,
        name="enclosure_netbox_comparisons",
    ),
    re_path(
        r"^enclosure/(?P<id>[0-9]+)/fetch-netbox$",
        views.enclosure_fetch_netbox,
        name="enclosure_netbox_fetch",
    ),
    re_path(
        r"^enclosure/(?P<id>[0-9]+)/compare-netbox$",
        views.enclosure_compare_netbox,
        name="enclosure_netbox_compare",
    ),
    path("enclosures/new", views.NewEnclosure.as_view(), name="new_enclosure"),
    path(
        "enclosures/delete/<int:pk>/",
        views.DeleteEnclosure.as_view(),
        name="delete_enclosure",
    ),
    path(
        "enclosures/edit/<int:pk>/",
        views.EnclosureDetailedEdit.as_view(),
        name="edit_enclosure",
    ),
    path(
        "remote-power-devices",
        views.RemotePowerDevicesListView.as_view(),
        name="remotepowerdevices",
    ),
    re_path(
        r"^remote-power-devices/(?P<id>[0-9]+)/detail$",
        views.remotepowerdevice_detail,
        name="remotepowerdevice_detail",
    ),
    re_path(
        r"^remote-power-devices/(?P<id>[0-9]+)/netboxcomparison$",
        views.remotepowerdevice_netboxcomparison,
        name="remotepowerdevice_netbox_comparisons",
    ),
    re_path(
        r"^remote-power-devices/(?P<id>[0-9]+)/fetch-netbox$",
        views.remotepowerdevice_fetch_netbox,
        name="remotepowerdevice_netbox_fetch",
    ),
    re_path(
        r"^remote-power-devices/(?P<id>[0-9]+)/compare-netbox$",
        views.remotepowerdevice_compare_netbox,
        name="remotepowerdevice_netbox_compare",
    ),
    path(
        "remote-power-devices/new",
        views.NewRemotePowerDevice.as_view(),
        name="new_remotepowerdevice",
    ),
    path(
        "remote-power-devices/delete/<int:pk>/",
        views.DeleteRemotePowerDevice.as_view(),
        name="delete_remotepowerdevice",
    ),
    path(
        "remote-power-devices/edit/<int:pk>/",
        views.RemotePowerDeviceDetailedEdit.as_view(),
        name="edit_remotepowerdevice",
    ),
    re_path(
        r"^$", RedirectView.as_view(pattern_name="frontend:free_machines"), name="root"
    ),
    re_path(
        r"^machines$",
        RedirectView.as_view(pattern_name="frontend:free_machines"),
        name="free_machines",
    ),
    re_path(r"^machines/all$", views.AllMachineListView.as_view(), name="machines"),
    re_path(
        r"^machines/free$", views.FreeMachineListView.as_view(), name="free_machines"
    ),
    re_path(r"^machines/my$", views.MyMachineListView.as_view(), name="my_machines"),
    re_path(
        r"^machines/virtualmachines$",
        views.VirtualMachineListView.as_view(),
        name="virtual_machines",
    ),
    re_path(r"^machines/search", views.machine_search, name="advanced_search"),
    path("machine/add", views.machine_add, name="machine_add"),
    re_path(r"^machine/(?P<id>[0-9]+)/$", views.machine, name="detail"),
    re_path(r"^machine/(?P<id>[0-9]+)/detail$", views.machine, name="detail"),
    re_path(r"^machine/(?P<id>[0-9]+)/cpu$", views.cpu, name="cpu"),
    re_path(
        r"^machine/(?P<id>[0-9]+)/networkinterfaces$",
        views.networkinterfaces,
        name="networkinterfaces",
    ),
    path(
        "networkinterface/delete/<int:pk>/",
        views.DeleteNetworkInterface.as_view(),
        name="delete_networkinterface",
    ),
    re_path(r"^machine/(?P<id>[0-9]+)/pci$", views.pci, name="pci"),
    re_path(
        r"^machine/(?P<id>[0-9]+)/installations$",
        views.installations,
        name="installations",
    ),
    re_path(r"^machine/(?P<id>[0-9]+)/usb$", views.usb, name="usb"),
    re_path(r"^machine/(?P<id>[0-9]+)/scsi$", views.scsi, name="scsi"),
    re_path(r"^machine/(?P<id>[0-9]+)/miscellaneous$", views.misc, name="misc"),
    re_path(r"^machine/(?P<id>[0-9]+)/history$", views.history, name="history"),
    re_path(
        r"^machine/(?P<id>[0-9]+)/ansible-results$",
        views.machine_ansible_results,
        name="machine_ansible_results",
    ),
    re_path(
        r"^machine/(?P<id>[0-9]+)/netboxcomparision$",
        views.machine_netboxcomparision,
        name="netboxcomparision",
    ),
    re_path(
        r"^machine/(?P<id>[0-9]+)/reserve$",
        views.machine_reserve,
        name="reserve_machine",
    ),
    re_path(
        r"^machine/(?P<id>[0-9]+)/release$",
        views.machine_release,
        name="release_machine",
    ),
    re_path(r"^machine/(?P<id>[0-9]+)/rescan$", views.rescan, name="rescan"),
    re_path(
        r"^machine/(?P<id>[0-9]+)/fetch-netbox$",
        views.fetch_netbox,
        name="netbox_fetch",
    ),
    re_path(
        r"^machine/(?P<id>[0-9]+)/compare-netbox$",
        views.compare_netbox,
        name="netbox_compare",
    ),
    re_path(
        r"^machine/(?P<id>[0-9]+)/cobbler-cleanup$",
        views.cobbler_cleanup,
        name="cleanup_domain_cobbler_page",
    ),
    re_path(r"^machine/(?P<id>[0-9]+)/setup$", views.setup, name="setup"),
    re_path(
        r"^machine/(?P<id>[0-9]+)/virtualization$",
        views.virtualization,
        name="virtualization",
    ),
    re_path(
        r"^machine/(?P<id>[0-9]+)/virtualization/add$",
        views.virtualization_add,
        name="virtualization_add",
    ),
    re_path(r"^login/$", views.login, name="login"),
    re_path(
        r"^logout/$", auth_views.LogoutView.as_view(), {"next_page": "/"}, name="logout"
    ),
    path("users", views.UserListView.as_view(), name="users"),
    re_path(
        r"^user/(?P<id>[0-9]+)/detail$",
        views.user_detail,
        name="user_detail",
    ),
    re_path(
        r"^user/(?P<id>[0-9]+)/reservations$",
        views.user_reservations,
        name="user_reservations",
    ),
    re_path(
        r"^user/(?P<id>[0-9]+)/reserve$",
        views.user_reserve_machine,
        name="user_reserve_machine",
    ),
    re_path(r"^user/create$", views.users_create, name="create_user"),
    re_path(r"^user/preferences$", views.users_preferences, name="preferences_user"),
    re_path(
        r"^password/restore$", views.users_password_restore, name="password_restore"
    ),
    re_path(r"^statistics$", views.statistics, name="statistics"),
    re_path(
        r"^ajax/machine/(?P<machine_id>[0-9]+)/annotation/add",
        views.ajax.annotation,
        name="ajax_annotation",
    ),
    re_path(
        r"^ajax/machine/(?P<machine_id>[0-9]+)/powercycle$",
        views.ajax.powercycle,
        name="ajax_powercycle",
    ),
    re_path(
        r"^ajax/machine/(?P<machine_id>[0-9]+)/sol/deactivate$",
        views.ajax.deactivate_sol,
        name="ajax_deactivate_sol",
    ),
    re_path(
        r"^ajax/machine/(?P<host_id>[0-9]+)/virtualization/list$",
        views.ajax.virtualization_list,
        name="ajax_virtualization_list",
    ),
    re_path(
        r"^ajax/machine/(?P<host_id>[0-9]+)/virtualization/delete$",
        views.ajax.virtualization_delete,
        name="ajax_virtualization_delete",
    ),
    path("regenerate/cobbler", views.regenerate_cobbler, name="regenerate_cobbler"),
    re_path(
        r"^regenerate/domain/cscreen/(?P<host_id>[0-9]+)$",
        views.regenerate.regenerate_domain_cscreen,
        name="regenerate_domain_cscreen",
    ),
    re_path(
        r"^regenerate/domain/cobbler/(?P<host_id>[0-9]+)$",
        views.regenerate.regenerate_domain_cobbler,
        name="regenerate_domain_cobbler",
    ),
    re_path(
        r"^regenerate/machine/cobbler/(?P<host_id>[0-9]+)$",
        views.regenerate.regenerate_machine_cobbler,
        name="regenerate_machine_cobbler",
    ),
    re_path(
        r"^regenerate/machine/motd/(?P<host_id>[0-9]+)$",
        views.regenerate.regenerate_machine_motd,
        name="regenerate_machine_motd",
    ),
    re_path(
        r"^regenerate/remote-power-device/cobbler/(?P<device_id>[0-9]+)$",
        views.regenerate.regenerate_remotepowerdevice_cobbler,
        name="regenerate_remotepowerdevice_cobbler",
    ),
    re_path(
        r"^compare-netbox/overview",
        views.NetboxOrthosComparisionRunListView.as_view(),
        name="compare_netbox_overview",
    ),
    re_path(
        r"^compare-netbox/(?P<id>[a-z0-9\-]+)$",
        views.netboxorthoscomparisonrun,
        name="compare_netbox_details",
    ),
    # Ansible Results
    path(
        "ansible-results",
        views.AnsibleResultListView.as_view(),
        name="ansible_results_list",
    ),
    re_path(
        r"^ansible-results/(?P<pk>[0-9]+)$",
        views.ansible_result_detail,
        name="ansible_result_detail",
    ),
    re_path(
        r"^ansible-results/(?P<pk>[0-9]+)/delete$",
        views.ansible_result_delete,
        name="ansible_result_delete",
    ),
    re_path(
        r"^ansible-results/(?P<pk>[0-9]+)/apply$",
        views.ansible_result_apply,
        name="ansible_result_apply",
    ),
    path(
        "ansible-results/bulk-delete",
        views.ansible_result_bulk_delete,
        name="ansible_results_bulk_delete",
    ),
    # Manufacturers
    path("manufacturers", views.ManufacturerListView.as_view(), name="manufacturers"),
    re_path(
        r"^manufacturers/(?P<id>[0-9]+)/detail$",
        views.manufacturer_detail,
        name="manufacturer_detail",
    ),
    re_path(
        r"^manufacturers/(?P<id>[0-9]+)/devicetypes$",
        views.manufacturer_device_types,
        name="manufacturer_device_types",
    ),
    re_path(
        r"^manufacturers/(?P<id>[0-9]+)/fetch-netbox$",
        views.manufacturer_fetch_netbox,
        name="manufacturer_netbox_fetch",
    ),
    re_path(
        r"^manufacturers/(?P<id>[0-9]+)/netboxcomparison$",
        views.manufacturer_netboxcomparison,
        name="manufacturer_netbox_comparisons",
    ),
    re_path(
        r"^manufacturers/(?P<id>[0-9]+)/compare-netbox$",
        views.manufacturer_compare_netbox,
        name="manufacturer_netbox_compare",
    ),
    path("manufacturers/new", views.NewManufacturer.as_view(), name="new_manufacturer"),
    path(
        "manufacturers/edit/<int:pk>/",
        views.ManufacturerDetailedEdit.as_view(),
        name="edit_manufacturer",
    ),
    path(
        "manufacturers/delete/<int:pk>/",
        views.DeleteManufacturer.as_view(),
        name="delete_manufacturer",
    ),
    # Device Types
    path("devicetypes", views.DeviceTypeListView.as_view(), name="devicetypes"),
    re_path(
        r"^devicetype/(?P<id>[0-9]+)/detail$",
        views.devicetype_detail,
        name="devicetype_detail",
    ),
    re_path(
        r"^devicetype/(?P<id>[0-9]+)/fetch-netbox$",
        views.devicetype_fetch_netbox,
        name="devicetype_netbox_fetch",
    ),
    re_path(
        r"^devicetype/(?P<id>[0-9]+)/netboxcomparison$",
        views.devicetype_netboxcomparison,
        name="devicetype_netbox_comparisons",
    ),
    re_path(
        r"^devicetype/(?P<id>[0-9]+)/compare-netbox$",
        views.devicetype_compare_netbox,
        name="devicetype_netbox_compare",
    ),
    path("devicetypes/new", views.NewDeviceType.as_view(), name="new_devicetype"),
    path(
        "devicetypes/edit/<int:pk>/",
        views.DeviceTypeDetailedEdit.as_view(),
        name="edit_devicetype",
    ),
    path(
        "devicetypes/delete/<int:pk>/",
        views.DeleteDeviceType.as_view(),
        name="delete_devicetype",
    ),
    # Serial Console Types
    path(
        "serialconsoletypes",
        views.SerialConsoleTypeListView.as_view(),
        name="serialconsoletypes",
    ),
    re_path(
        r"^serialconsoletype/(?P<id>[0-9]+)/detail$",
        views.serialconsoletype_detail,
        name="serialconsoletype_detail",
    ),
    path(
        "serialconsoletypes/new",
        views.NewSerialConsoleType.as_view(),
        name="new_serialconsoletype",
    ),
    path(
        "serialconsoletypes/edit/<int:pk>/",
        views.SerialConsoleTypeDetailedEdit.as_view(),
        name="edit_serialconsoletype",
    ),
    path(
        "serialconsoletypes/delete/<int:pk>/",
        views.DeleteSerialConsoleType.as_view(),
        name="delete_serialconsoletype",
    ),
    # Systems
    path("systems", views.SystemListView.as_view(), name="systems"),
    re_path(
        r"^system/(?P<id>[0-9]+)/detail$",
        views.system_detail,
        name="system_detail",
    ),
    path("systems/new", views.NewSystem.as_view(), name="new_system"),
    path(
        "systems/edit/<int:pk>/",
        views.SystemDetailedEdit.as_view(),
        name="edit_system",
    ),
    path(
        "systems/delete/<int:pk>/",
        views.DeleteSystem.as_view(),
        name="delete_system",
    ),
    # Single Tasks
    path("singletasks", views.SingleTaskListView.as_view(), name="singletasks"),
    re_path(
        r"^singletask/(?P<id>[0-9]+)/detail$",
        views.singletask_detail,
        name="singletask_detail",
    ),
    path("singletasks/new", views.NewSingleTask.as_view(), name="new_singletask"),
    path(
        "singletasks/edit/<int:pk>/",
        views.SingleTaskDetailedEdit.as_view(),
        name="edit_singletask",
    ),
    path(
        "singletasks/delete/<int:pk>/",
        views.DeleteSingleTask.as_view(),
        name="delete_singletask",
    ),
    # Daily Tasks
    path("dailytasks", views.DailyTaskListView.as_view(), name="dailytasks"),
    re_path(
        r"^dailytask/(?P<id>[0-9]+)/detail$",
        views.dailytask_detail,
        name="dailytask_detail",
    ),
    path("dailytasks/new", views.NewDailyTask.as_view(), name="new_dailytask"),
    path(
        "dailytasks/edit/<int:pk>/",
        views.DailyTaskDetailedEdit.as_view(),
        name="edit_dailytask",
    ),
    path(
        "dailytasks/delete/<int:pk>/",
        views.DeleteDailyTask.as_view(),
        name="delete_dailytask",
    ),
    path(
        "dailytask/<int:id>/execute/",
        views.dailytask_execute,
        name="dailytask_execute",
    ),
    path(
        "dailytask/<int:id>/switch/",
        views.dailytask_switch,
        name="dailytask_switch",
    ),
    # Remote Power Types
    path(
        "remotepowertypes",
        views.RemotePowerTypeListView.as_view(),
        name="remotepowertypes",
    ),
    re_path(
        r"^remotepowertype/(?P<id>[0-9]+)/detail$",
        views.remotepowertype_detail,
        name="remotepowertype_detail",
    ),
    path(
        "remotepowertypes/new",
        views.NewRemotePowerType.as_view(),
        name="new_remotepowertype",
    ),
    path(
        "remotepowertypes/edit/<int:pk>/",
        views.RemotePowerTypeDetailedEdit.as_view(),
        name="edit_remotepowertype",
    ),
    path(
        "remotepowertypes/delete/<int:pk>/",
        views.DeleteRemotePowerType.as_view(),
        name="delete_remotepowertype",
    ),
    # Architectures
    path("architectures", views.ArchitectureListView.as_view(), name="architectures"),
    re_path(
        r"^architecture/(?P<id>[0-9]+)/detail$",
        views.architecture_detail,
        name="architecture_detail",
    ),
    path("architectures/new", views.NewArchitecture.as_view(), name="new_architecture"),
    path(
        "architectures/edit/<int:pk>/",
        views.ArchitectureDetailedEdit.as_view(),
        name="edit_architecture",
    ),
    path(
        "architectures/delete/<int:pk>/",
        views.DeleteArchitecture.as_view(),
        name="delete_architecture",
    ),
    # Server Configuration
    path("serverconfigs", views.ServerConfigListView.as_view(), name="serverconfigs"),
    re_path(
        r"^serverconfig/(?P<id>[0-9]+)/detail$",
        views.serverconfig_detail,
        name="serverconfig_detail",
    ),
    path("serverconfigs/new", views.NewServerConfig.as_view(), name="new_serverconfig"),
    path(
        "serverconfigs/edit/<int:pk>/",
        views.ServerConfigDetailedEdit.as_view(),
        name="edit_serverconfig",
    ),
    path(
        "serverconfigs/delete/<int:pk>/",
        views.DeleteServerConfig.as_view(),
        name="delete_serverconfig",
    ),
]
