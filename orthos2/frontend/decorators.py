from typing import Callable, Concatenate, ParamSpec, TypeVar

from django.core.exceptions import BadRequest, PermissionDenied
from django.http import Http404, HttpRequest

from orthos2.data.models import Machine

P = ParamSpec("P")
R = TypeVar("R")


def check_permissions(
    key: str = "id",
) -> Callable[
    [Callable[Concatenate[HttpRequest, P], R]], Callable[Concatenate[HttpRequest, P], R]
]:
    def decorator(
        function: Callable[Concatenate[HttpRequest, P], R]
    ) -> Callable[Concatenate[HttpRequest, P], R]:
        def wrapper(request: HttpRequest, *args: P.args, **kwargs: P.kwargs) -> R:
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
                elif key in ("id", "machine_id"):
                    if not isinstance(ident, (str, int)):
                        raise PermissionDenied(
                            'Bad type of key "%s" must be int or str.', key
                        )
                    machine = Machine.objects.get(pk=ident)
                else:
                    raise BadRequest("Incorrect key given!")
            except Machine.DoesNotExist:
                raise Http404("Machine does not exist!")

            if machine.administrative or machine.system.administrative:
                if not request.user.is_superuser:  # type: ignore
                    raise PermissionDenied("Machine is administrative!")
            return function(request, *args, **kwargs)

        return wrapper

    return decorator
