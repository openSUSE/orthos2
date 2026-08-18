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
urlpatterns += ManufacturerInfoCommand.get_urls()  # noqa: F405
urlpatterns += DeviceTypeInfoCommand.get_urls()  # noqa: F405
urlpatterns += SerialConsoleTypeInfoCommand.get_urls()  # noqa: F405
urlpatterns += SystemInfoCommand.get_urls()  # noqa: F405
urlpatterns += SingleTaskInfoCommand.get_urls()  # noqa: F405
urlpatterns += DailyTaskInfoCommand.get_urls()  # noqa: F405
urlpatterns += RemotePowerTypeInfoCommand.get_urls()  # noqa: F405
urlpatterns += ArchitectureInfoCommand.get_urls()  # noqa: F405
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
urlpatterns += AddManufacturerCommand.get_urls()  # noqa: F405
urlpatterns += AddDeviceTypeCommand.get_urls()  # noqa: F405
urlpatterns += AddSerialConsoleTypeCommand.get_urls()  # noqa: F405
urlpatterns += AddSystemCommand.get_urls()  # noqa: F405
urlpatterns += AddSingleTaskCommand.get_urls()  # noqa: F405
urlpatterns += AddDailyTaskCommand.get_urls()  # noqa: F405
urlpatterns += AddRemotePowerTypeCommand.get_urls()  # noqa: F405
urlpatterns += AddArchitectureCommand.get_urls()  # noqa: F405
urlpatterns += AddServerConfigCommand.get_urls()  # noqa: F405
urlpatterns += AddEnclosureCommand.get_urls()  # noqa: F405
urlpatterns += DeleteCommand.get_urls()  # noqa: F405
urlpatterns += DeleteMachineCommand.get_urls()  # noqa: F405
urlpatterns += DeleteSerialConsoleCommand.get_urls()  # noqa: F405
urlpatterns += DeleteRemotePowerCommand.get_urls()  # noqa: F405
urlpatterns += DeleteRemotePowerDeviceCommand.get_urls()  # noqa: F405
urlpatterns += DeleteNetworkInterfaceCommand.get_urls()  # noqa: F405
urlpatterns += DeleteManufacturerCommand.get_urls()  # noqa: F405
urlpatterns += DeleteDeviceTypeCommand.get_urls()  # noqa: F405
urlpatterns += DeleteSerialConsoleTypeCommand.get_urls()  # noqa: F405
urlpatterns += DeleteSystemCommand.get_urls()  # noqa: F405
urlpatterns += DeleteSingleTaskCommand.get_urls()  # noqa: F405
urlpatterns += DeleteDailyTaskCommand.get_urls()  # noqa: F405
urlpatterns += DeleteRemotePowerTypeCommand.get_urls()  # noqa: F405
urlpatterns += DeleteArchitectureCommand.get_urls()  # noqa: F405
urlpatterns += DeleteServerConfigCommand.get_urls()  # noqa: F405
urlpatterns += DeleteEnclosureCommand.get_urls()  # noqa: F405
urlpatterns += EditCommand.get_urls()  # noqa: F405
urlpatterns += EditManufacturerCommand.get_urls()  # noqa: F405
urlpatterns += EditDeviceTypeCommand.get_urls()  # noqa: F405
urlpatterns += EditSerialConsoleTypeCommand.get_urls()  # noqa: F405
urlpatterns += EditSystemCommand.get_urls()  # noqa: F405
urlpatterns += EditSingleTaskCommand.get_urls()  # noqa: F405
urlpatterns += EditDailyTaskCommand.get_urls()  # noqa: F405
urlpatterns += ExecuteDailyTaskCommand.get_urls()  # noqa: F405
urlpatterns += SwitchDailyTaskCommand.get_urls()  # noqa: F405
urlpatterns += EditRemotePowerTypeCommand.get_urls()  # noqa: F405
urlpatterns += EditArchitectureCommand.get_urls()  # noqa: F405
urlpatterns += EditServerConfigCommand.get_urls()  # noqa: F405
urlpatterns += EditEnclosureCommand.get_urls()  # noqa: F405
urlpatterns += EditRemotePowerDeviceCommand.get_urls()  # noqa: F405
