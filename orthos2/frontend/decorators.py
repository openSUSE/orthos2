from django.core.exceptions import PermissionDenied
from django.http import Http404

from data.models import Machine


def check_permissions(key='id'):
    def decorator(function):
        def wrapper(request, *args, **kwargs):
            """
            Check access permission for machine.

            Only superusers can access administrative machines and/or systems.
            Raises `PermissionDenied` exception if a user is not authorized.
            """
            machine_id = kwargs.get(key, None)

            if machine_id is None:
                raise PermissionDenied("Can't get ID of machine")

            try:
                machine = Machine.objects.get(pk=machine_id)
            except Machine.DoesNotExist:
                raise Http404("Machine does not exist!")

            if machine.administrative or machine.system.administrative:
                if not request.user.is_superuser:
                    raise PermissionDenied("Machine is administrative!")
            return function(request, *args, **kwargs)

        return wrapper
    return decorator
