from django.core.exceptions import PermissionDenied
from django.http import Http404

from orthos2.data.models import Machine


def check_permissions(key="id"):
    def decorator(function):
        def wrapper(request, *args, **kwargs):
            """
            Check access permission for machine.

            Only superusers can access administrative machines and/or systems.
            Raises `PermissionDenied` exception if a user is not authorized.
            """
            try:
                ident = kwargs.get(key, None)
                if ident is None:
                    raise PermissionDenied("Bad key %s", key)
                if key == "fqdn":
                    machine = Machine.objects.get(fqdn=ident)
                elif key == "id":
                    machine = Machine.objects.get(pk=ident)
            except Machine.DoesNotExist:
                raise Http404("Machine does not exist!")

            if machine.administrative or machine.system.administrative:
                if not request.user.is_superuser:
                    raise PermissionDenied("Machine is administrative!")
            return function(request, *args, **kwargs)

        return wrapper

    return decorator
