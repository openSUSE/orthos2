from django.apps import AppConfig
from rest_framework.schemas.openapi import AutoSchema, SchemaGenerator


class OpenapiConfig(AppConfig):
    name = "openapi"


class CustomSchemaGenerator(SchemaGenerator):
    def get_schema(self, request=None, public=False):
        schema = super().get_schema(request, public)

        # Make sure components exist
        if "components" not in schema:
            schema["components"] = {}

        # Tells swagger to render the Authorize button and what to put it in
        schema["components"]["securitySchemes"] = {
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "Authorization",
                "description": 'Token format: "Token <your_token>"',
            }
        }

        schema["security"] = [{"ApiKeyAuth": []}]

        return schema


class CustomViewSchema(AutoSchema):
    def get_description(self, path, method):

        # Detailed help if available
        if hasattr(self.view, "HELP") and self.view.HELP:
            return self.view.HELP

        # Fallback to short help
        if hasattr(self.view, "HELP_SHORT") and self.view.HELP_SHORT:
            return self.view.HELP_SHORT

        # Fallback to default
        return super().get_description(path, method)

    def get_operation(self, path, method):
        operation = super().get_operation(path, method)

        if hasattr(self.view, "ARGUMENTS") and self.view.ARGUMENTS:

            # Flatten arguments
            flat_args = []
            for item in self.view.ARGUMENTS:
                if isinstance(item, (list, tuple)):
                    flat_args.extend(item)
                else:
                    flat_args.append(item)

            if method.upper() == "GET":

                # Make sure parameters exist
                if "parameters" not in operation:
                    operation["parameters"] = []

                # Build parameter object
                for arg_name in flat_args:
                    # Failsafe, string so Swagger doesn't panic
                    arg_name = str(arg_name).strip()

                    param = {
                        "name": arg_name,
                        "in": "query",
                        "schema": {"type": "string"},
                    }

                    # Add dropdown using tab completion list (and sort them)
                    if arg_name == "action" and hasattr(self.view, "get_tabcompletion"):
                        param["schema"]["enum"] = sorted(self.view.get_tabcompletion())

                    operation["parameters"].append(param)

            elif method.upper() in ["POST", "PUT", "PATCH"]:
                # Build properties dict
                properties = {}
                for arg_name in flat_args:
                    arg_name = str(arg_name).strip()

                    prop_schema = {"type": "string"}
                    if arg_name == "action" and hasattr(self.view, "get_tabcompletion"):
                        prop_schema["enum"] = sorted(self.view.get_tabcompletion())

                    properties[arg_name] = prop_schema

                # Tell Swagger to actually render the stuff
                operation["requestBody"] = {
                    "content": {
                        "application/json": {
                            "schema": {"type": "object", "properties": properties}
                        },
                        "application/x-www-form-urlencoded": {
                            "schema": {"type": "object", "properties": properties}
                        },
                    }
                }

        return operation

    # Resource-agnostic CLI dispatcher endpoints (ADD/DELETE/EDIT/QUERY/...) stay grouped
    # under "API" instead of being tagged by their own name.
    GENERIC_RESOURCE_SEGMENTS = {
        "add",
        "delete",
        "edit",
        "query",
        "reserve",
        "release",
        "regenerate",
        "rescan",
        "setup",
        "powercycle",
        "login",
        "schema",
    }

    def get_tags(self, path, method):
        # Grabs URL and splits it by /
        path_segments = [segment for segment in path.strip("/").split("/") if segment]

        # Exceptions for machine and remote power, whose multi-word names don't
        # capitalize cleanly (and some of their commands live at the api root).
        if "machine" in path_segments:
            return ["Machine"]

        if "remotepowerdevice" in path_segments:
            return ["RemotePowerDevice"]

        # Paths are always "/api/<resource>[/<action>]" — path_segments[0] is the
        # fixed "api" prefix, so the resource-identifying segment is the second one.
        if len(path_segments) < 2:
            return ["API"]

        resource = path_segments[1]

        if resource in self.GENERIC_RESOURCE_SEGMENTS:
            return ["API"]

        # Every other resource (e.g. /api/manufacturer, /api/manufacturer/add, /api/devicetype/edit)
        # gets its own tag/group instead of falling into a single catch-all "API" bucket.
        return [resource.capitalize()]
