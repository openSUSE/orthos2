"""
Read-only superuser view of social-django's OIDC handshake bookkeeping
tables (Association, Nonce). Neither is written or read by any Orthos2
code - they exist purely to support the OIDC login handshake, and this
view exists only so a superuser can inspect them while troubleshooting.
"""

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from social_django.models import Association, Nonce


@login_required
def oidc_diagnostics(request: HttpRequest) -> HttpResponse:
    if not request.user.is_superuser:  # type: ignore
        raise PermissionDenied

    return render(
        request,
        "frontend/oidc_diagnostics/oidc_diagnostics.html",
        {
            "associations": Association.objects.all().order_by("-issued"),
            "nonces": Nonce.objects.all().order_by("-timestamp"),
            "title": "OIDC Diagnostics",
        },
    )
