# pylint: skip-file

from django.urls import re_path
from rest_framework.authtoken import views as authtoken_views

from orthos2.api import views
from orthos2.api.commands import *  # noqa: F403

app_name = 'api'
urlpatterns = [
    re_path(r'^$', views.root, name='root'),
    re_path(r'^login', authtoken_views.obtain_auth_token),
]

urlpatterns += InfoCommand.get_urls()                   # noqa: F405
urlpatterns += QueryCommand.get_urls()                  # noqa: F405
urlpatterns += ReserveCommand.get_urls()                # noqa: F405
urlpatterns += ReleaseCommand.get_urls()                # noqa: F405
urlpatterns += ReservationHistoryCommand.get_urls()     # noqa: F405
urlpatterns += RescanCommand.get_urls()                 # noqa: F405
urlpatterns += RegenerateCommand.get_urls()             # noqa: F405
urlpatterns += ServerConfigCommand.get_urls()           # noqa: F405
urlpatterns += SetupCommand.get_urls()                  # noqa: F405
urlpatterns += PowerCommand.get_urls()                  # noqa: F405
urlpatterns += AddCommand.get_urls()                    # noqa: F405
urlpatterns += AddVMCommand.get_urls()                  # noqa: F405
urlpatterns += AddMachineCommand.get_urls()             # noqa: F405
urlpatterns += AddSerialConsoleCommand.get_urls()       # noqa: F405
urlpatterns += AddAnnotationCommand.get_urls()          # noqa: F405
urlpatterns += AddBMCCommand.get_urls()
urlpatterns += AddRemotePowerCommand.get_urls()         # noqa: F405
urlpatterns += AddRemotePowerDeviceCommand.get_urls()
urlpatterns += DeleteCommand.get_urls()                 # noqa: F405
urlpatterns += DeleteMachineCommand.get_urls()          # noqa: F405
urlpatterns += DeleteSerialConsoleCommand.get_urls()    # noqa: F405
urlpatterns += DeleteRemotePowerCommand.get_urls()      # noqa: F405
urlpatterns += DeleteRemotePowerDeviceCommand.get_urls()  # noda: F405
