from api.serializers.misc import RootSerializer
from data.models import ServerConfig
from django.conf import settings
from django.urls import reverse
from rest_framework.decorators import api_view


@api_view(["GET"])
def root(request):
    """API root."""
    import api.commands as commands

    data = {
        'version': settings.VERSION,
        'contact': settings.CONTACT,
        'api': request.build_absolute_uri(reverse('api:root')),
        'web': request.build_absolute_uri(reverse('frontend:root')),
        'message': ServerConfig.objects.by_key('orthos.api.welcomemessage'),
        'commands': {
            'info': commands.InfoCommand.description(),
            'query': commands.QueryCommand.description(),
            'reserve': commands.ReserveCommand.description(),
            'release': commands.ReleaseCommand.description(),
            'reservationhistory': commands.ReservationHistoryCommand.description(),
            'rescan': commands.RescanCommand.description(),
            'regenerate': commands.RegenerateCommand.description(),
            'serverconfig': commands.ServerConfigCommand.description(),
            'setup': commands.SetupCommand.description(),
            'power': commands.PowerCommand.description(),
            'add': commands.AddCommand.description(),
            'delete': commands.DeleteCommand.description(),
        }
    }
    root = RootSerializer(data)

    return root.as_json
