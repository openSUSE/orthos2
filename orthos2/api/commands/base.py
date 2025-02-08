import linecache
import sys
from typing import Any, Dict, List, Optional, Tuple, Union

from django.shortcuts import redirect
from django.urls import URLPattern
from rest_framework.views import APIView

from orthos2.api.serializers.misc import SelectSerializer
from orthos2.data.models import Machine


def getException() -> str:
    """
    Use this function to create error messages when an Exception happens during
    processing of client commands.
    Typically Exceptions during command processing are caught and returned like that:
        except Exception as e:
            logger.exception(e)
            return ErrorMessage(getException()).as_json

        return JsonResponse(response)
    """
    _exc_type, exc_obj, tb = sys.exc_info()
    if tb is None:
        return "EXCEPTION COULD NOT BE RETRIEVED"
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    return 'EXCEPTION IN ({}, LINE {} "{}"): {}'.format(
        filename, lineno, line.strip(), exc_obj
    )


def get_machine(
    fqdn: str,
    redirect_to: str,
    data: Optional[Any] = None,
    redirect_key_replace: str = "fqdn",
) -> Machine:
    """
    Look up FQDN in the database and return one machine object if found or raise corresponding
    exception if something went wrong.

    The hostname is often sufficient for the lookup, so try the hostname (hostname + '.') first.
    """
    if not fqdn:
        raise ValueError("Requires <fqdn> argument!")

    try:
        machines = [Machine.api.get(fqdn__startswith=fqdn + ".")]
    except Exception:
        machines = list(Machine.api.filter(fqdn__startswith=fqdn))

    if len(machines) == 1:
        machine = machines[0]
    elif machines:
        selection = SelectSerializer(machines, "Please specify:")  # type: ignore
        return selection  # type: ignore
    else:
        raise Exception("Machine '{}' does not exist!".format(fqdn))

    if fqdn != machine.fqdn:
        response = redirect(redirect_to)

        if data:
            if redirect_key_replace is not None:
                data = data.copy()
                data.__setitem__(redirect_key_replace, machine.fqdn)
            response["Location"] += "?{}".format(data.urlencode())

        return response  # type: ignore

    return machine


class BaseAPIView(APIView):
    METHOD = ""
    URL = ""
    ARGUMENTS: Tuple[List[str], ...] = tuple()
    HELP_SHORT = ""
    HELP = ""

    @staticmethod
    def get_urls() -> List[URLPattern]:
        raise NotImplementedError

    @staticmethod
    def get_tabcompletion() -> List[str]:
        return []

    @classmethod
    def description(cls) -> Dict[str, Union[str, List[str]]]:
        return {
            "help": cls.HELP_SHORT,
            "docstring": cls.HELP,
            "tabcompletion": cls.get_tabcompletion(),
            "url": cls.URL,
            "arguments": cls.ARGUMENTS,  # type: ignore
            "method": cls.METHOD,
        }
