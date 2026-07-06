# pylint: skip-file

from django.urls import path, re_path
from django.views.generic import TemplateView
from rest_framework.authtoken import views as authtoken_views
from rest_framework.schemas import get_schema_view

from orthos2.api import views
from orthos2.api.commands import *  # noqa: F403
from orthos2.api.schema import CustomSchemaGenerator

app_name = "api"
urlpatterns = [
    path(
        "schema/swagger-ui/",
        TemplateView.as_view(
            template_name="api/swagger-ui.html",
            extra_context={"schema_url": "api:openapi-schema"},
        ),
        name="swagger-ui",
    ),
    path(
        "schema",
        get_schema_view(
            title="Orthos2",
            description="API for Orthos2",
            version="1.10",
            generator_class=CustomSchemaGenerator,
        ),
        name="openapi-schema",
    ),
    re_path(r"^$", views.root, name="root"),
    re_path(r"^login", authtoken_views.obtain_auth_token),
]

urlpatterns += InfoCommand.get_urls()  # noqa: F405
urlpatterns += EnclosureInfoCommand.get_urls()  # noqa: F405
urlpatterns += RemotePowerDeviceInfoCommand.get_urls()  # noqa: F405
urlpatterns += QueryCommand.get_urls()  # noqa: F405
urlpatterns += ReserveCommandGet.get_urls()  # noqa: F405
urlpatterns += ReserveCommandPost.get_urls()  # noqa: F405
urlpatterns += ReleaseCommand.get_urls()  # noqa: F405
urlpatterns += ReservationHistoryCommand.get_urls()  # noqa: F405
urlpatterns += RescanCommand.get_urls()  # noqa: F405
urlpatterns += RegenerateCommand.get_urls()  # noqa: F405
urlpatterns += ServerConfigCommand.get_urls()  # noqa: F405
urlpatterns += SetupCommand.get_urls()  # noqa: F405
urlpatterns += PowerCommand.get_urls()  # noqa: F405
urlpatterns += AddCommand.get_urls()  # noqa: F405
urlpatterns += AddVMCommandGet.get_urls()  # noqa: F405
urlpatterns += AddVMCommandPost.get_urls()  # noqa: F405
urlpatterns += AddMachineCommand.get_urls()  # noqa: F405
urlpatterns += AddSerialConsoleCommandGet.get_urls()  # noqa: F405
urlpatterns += AddSerialConsoleCommandPost.get_urls()  # noqa: F405
urlpatterns += AddAnnotationCommandGet.get_urls()  # noqa: F405
urlpatterns += AddAnnotationCommandPost.get_urls()  # noqa: F405
urlpatterns += AddBMCCommandPost.get_urls()  # noqa: F405
urlpatterns += AddBMCCommandGet.get_urls()  # noqa: F405
urlpatterns += AddRemotePowerCommandPost.get_urls()  # noqa: F405
urlpatterns += AddRemotePowerCommandGet.get_urls()  # noqa: F405
urlpatterns += AddRemotePowerDeviceCommand.get_urls()  # noqa: F405
urlpatterns += DeleteCommand.get_urls()  # noqa: F405
urlpatterns += DeleteMachineCommand.get_urls()  # noqa: F405
urlpatterns += DeleteSerialConsoleCommand.get_urls()  # noqa: F405
urlpatterns += DeleteRemotePowerCommand.get_urls()  # noqa: F405
urlpatterns += DeleteRemotePowerDeviceCommand.get_urls()  # noqa: F405
urlpatterns += DeleteNetworkInterfaceCommand.get_urls()  # noqa: F405
