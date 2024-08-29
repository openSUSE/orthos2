from typing import Any, Dict, Optional

from django.contrib.admin import AdminSite
from django.http import HttpRequest
from django.template.response import TemplateResponse


class MyAdminSite(AdminSite):
    index_template = "admin/base.html"
    # Text to put at the end of each page's <title>.
    site_title = "Orthos2 site admin"
    # Text to put in each page's <h1>.
    site_header = "Orthos2 Administration"

    # C&P -> not sure this is needed
    def index(
        self, request: HttpRequest, extra_context: Optional[Dict[str, Any]] = None
    ) -> TemplateResponse:
        # Update extra_context with new variables
        return super().index(request, extra_context)
