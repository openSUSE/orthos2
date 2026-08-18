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
from orthos2.api.forms import VendorAPIForm
from orthos2.api.serializers.misc import (
    AuthRequiredSerializer,
    ErrorMessage,
    InputSerializer,
    Message,
)
from orthos2.data.models import Vendor
from orthos2.utils.misc import format_cli_form_errors

logger = logging.getLogger("api")


class Edit:
    VENDOR = "vendor"

    as_list = [VENDOR]


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

                vendor <id> : Edit a vendor (superusers only).

    Example:
        EDIT vendor 1
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

        if item == Edit.VENDOR:
            if len(sub_arguments) != 1:
                return ErrorMessage("Invalid number of arguments for 'vendor'!").as_json

            return redirect(
                "{}?id={}".format(reverse("api:vendor_edit"), sub_arguments[0])
            )

        return ErrorMessage("Unknown item '{}'!".format(item)).as_json


class EditVendorCommand(BaseAPIView):

    METHOD = "POST"
    URL = "/vendor/edit"
    URL_POST = "/vendor/edit"
    ARGUMENTS = (["id", "name"],)

    HELP_SHORT = "Edits a vendor in the database."
    HELP = """Edits a vendor in the database (superusers only).

    Usage:
        EDIT vendor <id>
    """

    @staticmethod
    def get_urls() -> List[URLPattern]:
        return [
            re_path(
                r"^vendor/edit",
                EditVendorCommand.as_view(),
                name="vendor_edit",
            ),
        ]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return form for editing a vendor."""
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        vendor_id = request.GET.get("id")
        try:
            vendor = Vendor.objects.get(pk=vendor_id)
        except (Vendor.DoesNotExist, ValueError, TypeError):
            return ErrorMessage(
                "Vendor with id '{}' does not exist!".format(vendor_id)
            ).as_json

        form = VendorAPIForm(instance=vendor)
        fields = form.as_dict()
        fields["id"] = {
            "type": "INTEGER",
            "prompt": "ID",
            "initial": vendor.pk,
            "required": True,
        }

        input = InputSerializer(fields, self.URL_POST, ["id"] + form.get_order())
        return input.as_json

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """Edit vendor."""
        if not request.user.is_superuser:  # type: ignore
            return ErrorMessage(
                "Only superusers are allowed to perform this action!"
            ).as_json

        data = json.loads(request.body.decode("utf-8"))["form"]
        vendor_id = data.get("id")
        try:
            vendor = Vendor.objects.get(pk=vendor_id)
        except (Vendor.DoesNotExist, ValueError, TypeError):
            return ErrorMessage(
                "Vendor with id '{}' does not exist!".format(vendor_id)
            ).as_json

        form = VendorAPIForm(data, instance=vendor)

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
