"""
Command classes for editing existing database objects via the API.
"""

import json
import logging
from typing import Any, List, Union

from django.contrib.auth.models import AnonymousUser
from django.http import (
    HttpResponsePermanentRedirect,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import redirect  # type: ignore
from django.urls import URLPattern, re_path, reverse  # type: ignore
from rest_framework.request import Request

from orthos2.api.commands.base import BaseAPIView
from orthos2.api.forms import ManufacturerAPIForm, PlatformAPIForm
from orthos2.api.serializers.misc import (
    AuthRequiredSerializer,
    ErrorMessage,
    InputSerializer,
    Message,
)
from orthos2.data.models import Manufacturer, Platform
from orthos2.utils.misc import format_cli_form_errors

logger = logging.getLogger("api")


class Edit:
    MANUFACTURER = "manufacturer"
    PLATFORM = "platform"

    as_list = [MANUFACTURER, PLATFORM]


class EditCommand(BaseAPIView):

    METHOD = "GET"
    URL = "/edit"
    ARGUMENTS = (["args*"],)

    HELP_SHORT = "Edits information in the database."
    HELP = """Edits items in the database. All information will be queried interactively.

    Usage:
        EDIT <item> [args*]

    Arguments:
        item - Specify the item which should be edited. Items are:

                manufacturer <id> : Edit a manufacturer (superusers only).
                platform <id>     : Edit a platform (superusers only).

    Example:
        EDIT manufacturer 1
        EDIT platform 1
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(r"^edit$", EditCommand.as_view(), name="edit"),
        ]

    @staticmethod
    def get_tabcompletion() -> List[str]:
        return Edit.as_list

    def get(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> Union[JsonResponse, HttpResponsePermanentRedirect, HttpResponseRedirect]:
        """Dispatcher for the 'edit' command."""
        arguments = request.GET.get("args", None)

        if arguments:
            arguments = arguments.split()  # type: ignore
            item = arguments[0].lower()
            sub_arguments = arguments[1:]
        else:
            return ErrorMessage("Item is missing!").as_json

        if item == Edit.MANUFACTURER:
            if len(sub_arguments) != 1:
                return ErrorMessage(
                    "Invalid number of arguments for 'manufacturer'!"
                ).as_json

            return redirect(
                "{}?id={}".format(reverse("api:manufacturer_edit"), sub_arguments[0])
            )

        elif item == Edit.PLATFORM:
            if len(sub_arguments) != 1:
                return ErrorMessage(
                    "Invalid number of arguments for 'platform'!"
                ).as_json

            return redirect(
                "{}?id={}".format(reverse("api:platform_edit"), sub_arguments[0])
            )

        return ErrorMessage("Unknown item '{}'!".format(item)).as_json


class EditManufacturerCommand(BaseAPIView):

    METHOD = "POST"
    URL = "/manufacturer/edit"
    URL_POST = "/manufacturer/edit"
    ARGUMENTS = (["id", "name"],)

    HELP_SHORT = "Edits a manufacturer in the database."
    HELP = """Edits a manufacturer in the database (superusers only).

    Usage:
        EDIT manufacturer <id>
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^manufacturer/edit",
                EditManufacturerCommand.as_view(),
                name="manufacturer_edit",
            ),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return form for editing a manufacturer."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        manufacturer_id = request.GET.get("id")
        try:
            manufacturer = Manufacturer.objects.get(pk=manufacturer_id)  # type: ignore[misc]
        except (Manufacturer.DoesNotExist, ValueError, TypeError):
            return ErrorMessage(
                "Manufacturer with id '{}' does not exist!".format(manufacturer_id)
            ).as_json

        form = ManufacturerAPIForm(instance=manufacturer)
        fields = form.as_dict()
        fields["id"] = {
            "type": "INTEGER",
            "prompt": "ID",
            "initial": manufacturer.pk,
            "required": True,
        }

        input = InputSerializer(fields, self.URL_POST, ["id"] + form.get_order())
        return input.as_json

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Edit manufacturer."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        manufacturer_id = data.get("id")
        try:
            manufacturer = Manufacturer.objects.get(pk=manufacturer_id)
        except (Manufacturer.DoesNotExist, ValueError, TypeError):
            return ErrorMessage(
                "Manufacturer with id '{}' does not exist!".format(manufacturer_id)
            ).as_json

        form = ManufacturerAPIForm(data, instance=manufacturer)

        if form.is_valid():
            try:
                form.save()
            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

            return Message("Ok.").as_json

        return ErrorMessage(
            "\n{}".format(format_cli_form_errors(form))  # type: ignore[arg-type]
        ).as_json


class EditPlatformCommand(BaseAPIView):

    METHOD = "POST"
    URL = "/platform/edit"
    URL_POST = "/platform/edit"
    ARGUMENTS = (["id", "name", "manufacturer", "is_cartridge", "description"],)

    HELP_SHORT = "Edits a platform in the database."
    HELP = """Edits a platform in the database (superusers only).

    Usage:
        EDIT platform <id>
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^platform/edit",
                EditPlatformCommand.as_view(),
                name="platform_edit",
            ),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return form for editing a platform."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        platform_id = request.GET.get("id")
        try:
            platform = Platform.objects.get(pk=platform_id)
        except (Platform.DoesNotExist, ValueError, TypeError):
            return ErrorMessage(
                "Platform with id '{}' does not exist!".format(platform_id)
            ).as_json

        form = PlatformAPIForm(instance=platform)
        fields = form.as_dict()
        fields["id"] = {
            "type": "INTEGER",
            "prompt": "ID",
            "initial": platform.pk,
            "required": True,
        }

        input = InputSerializer(fields, self.URL_POST, ["id"] + form.get_order())
        return input.as_json

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Edit platform."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        platform_id = data.get("id")
        try:
            platform = Platform.objects.get(pk=platform_id)
        except (Platform.DoesNotExist, ValueError, TypeError):
            return ErrorMessage(
                "Platform with id '{}' does not exist!".format(platform_id)
            ).as_json

        form = PlatformAPIForm(data, instance=platform)

        if form.is_valid():
            try:
                form.save()
            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

            return Message("Ok.").as_json

        return ErrorMessage(
            "\n{}".format(format_cli_form_errors(form))  # type: ignore[arg-type]
        ).as_json
