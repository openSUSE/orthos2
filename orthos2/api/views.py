from typing import Any, Dict

from django.conf import settings
from django.http import HttpRequest, JsonResponse
from django.urls import reverse  # type: ignore
from rest_framework.decorators import api_view

from orthos2.api.serializers.misc import RootSerializer
from orthos2.data.models import ServerConfig


@api_view(["GET"])
def root(request: HttpRequest) -> JsonResponse:
    """API root."""
    import orthos2.api.commands as commands

    data: Dict[str, Any] = {
        "version": settings.VERSION,
        "contact": settings.CONTACT,
        "user": request.user.username,  # type: ignore
        "api": request.build_absolute_uri(reverse("api:root")),
        "web": request.build_absolute_uri(reverse("frontend:root")),
        "message": ServerConfig.get_server_config_manager().by_key(
            "orthos.api.welcomemessage", "Come in, reserve and play..."
        ),
        "commands": {
            "info": commands.InfoCommand.description(),
            "query": commands.QueryCommand.description(),
            "reserve": commands.ReserveCommand.description(),
            "release": commands.ReleaseCommand.description(),
            "reservationhistory": commands.ReservationHistoryCommand.description(),
            "rescan": commands.RescanCommand.description(),
            "regenerate": commands.RegenerateCommand.description(),
            "serverconfig": commands.ServerConfigCommand.description(),
            "setup": commands.SetupCommand.description(),
            "power": commands.PowerCommand.description(),
            "add": commands.AddCommand.description(),
            "delete": commands.DeleteCommand.description(),
        },
    }
    root = RootSerializer(data)

    return root.as_json
