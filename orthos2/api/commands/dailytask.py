"""
Command classes for the DailyTask "execute now" and "enable/disable" actions that used to be
custom Django Admin buttons on DailyTaskAdmin.
"""

from datetime import timedelta
from typing import Any, List

from django.contrib.auth.models import AnonymousUser
from django.http import JsonResponse
from django.urls import URLPattern, re_path  # type: ignore
from django.utils import timezone
from rest_framework.request import Request

from orthos2.api.commands.base import BaseAPIView
from orthos2.api.serializers.misc import AuthRequiredSerializer, ErrorMessage, Message
from orthos2.taskmanager.models import DailyTask


class ExecuteDailyTaskCommand(BaseAPIView):

    METHOD = "POST"
    URL = "/dailytask/{id}/execute"
    ARGUMENTS = (["id"],)

    HELP_SHORT = "Forces immediate execution of a daily task."
    HELP = """Forces a daily task to run on the taskmanager's next poll, by backdating its
    last execution date (superusers only).

    Usage:
        EXECUTE dailytask <id>
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^dailytask/(?P<id>[0-9]+)/execute$",
                ExecuteDailyTaskCommand.as_view(),
                name="dailytask_execute",
            ),
        ]

    def post(
        self, request: Request, id: int, *args: Any, **kwargs: Any
    ) -> JsonResponse:
        """Force a daily task to execute on the taskmanager's next poll."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        try:
            task = DailyTask.objects.get(pk=id)
        except (DailyTask.DoesNotExist, ValueError, TypeError):
            return ErrorMessage(
                "Daily task with id '{}' does not exist!".format(id)
            ).as_json

        if not task.enabled:
            return ErrorMessage(
                "Daily task '{}' is disabled.".format(task.name)
            ).as_json

        if task.running:
            return ErrorMessage("Task is already running!").as_json

        task.executed_at = timezone.now() - timedelta(days=1)
        task.save()

        return Message("Executing daily task '{}'...".format(task.name)).as_json


class SwitchDailyTaskCommand(BaseAPIView):

    METHOD = "POST"
    URL = "/dailytask/{id}/switch"
    ARGUMENTS = (["id", "action"],)

    HELP_SHORT = "Enables or disables a daily task."
    HELP = """Enables or disables a daily task (superusers only).

    Usage:
        SWITCH dailytask <id> <action>

    Arguments:
        action - "enable" or "disable"
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^dailytask/(?P<id>[0-9]+)/switch$",
                SwitchDailyTaskCommand.as_view(),
                name="dailytask_switch",
            ),
        ]

    def post(
        self, request: Request, id: int, *args: Any, **kwargs: Any
    ) -> JsonResponse:
        """Enable or disable a daily task."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        try:
            task = DailyTask.objects.get(pk=id)
        except (DailyTask.DoesNotExist, ValueError, TypeError):
            return ErrorMessage(
                "Daily task with id '{}' does not exist!".format(id)
            ).as_json

        action = request.data.get("action")  # type: ignore[attr-defined]

        if action == "enable":
            task.enabled = True
            # Prevent the task from starting to run immediately.
            task.executed_at = timezone.now()
        elif action == "disable":
            task.enabled = False
            task.running = False
        else:
            return ErrorMessage("Unknown action '{}'!".format(action)).as_json

        task.save()

        return Message("Successfully {}d task '{}'.".format(action, task.name)).as_json
