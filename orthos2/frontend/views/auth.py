"""
All views that are related to built-in authentication.
"""

import functools
import warnings
from typing import Any, Callable, Union

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth import login as auth_login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpRequest, HttpResponsePermanentRedirect, HttpResponseRedirect
from django.shortcuts import redirect, resolve_url
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.safestring import mark_safe
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters

from orthos2.data.models import ServerConfig


def deprecate_current_app(func: Callable[[Any, Any], Any]) -> Callable[[Any, Any], Any]:
    """Handle deprecation of the current_app parameter of the views."""

    @functools.wraps(func)
    def inner(*args: Any, **kwargs: Any) -> Any:
        if "current_app" in kwargs:
            warnings.warn(
                "Passing `current_app` as a keyword argument is deprecated. "
                "Instead the caller of `{0}` should set "
                "`request.current_app`.".format(func.__name__)
            )
            current_app = kwargs.pop("current_app")
            request = kwargs.get("request", None)
            if request and current_app is not None:
                request.current_app = current_app
        return func(*args, **kwargs)

    return inner


def _get_login_redirect_url(request: HttpRequest, redirect_to: str) -> str:
    # Ensure the user-originating redirection URL is safe.
    if not url_has_allowed_host_and_scheme(url=redirect_to, host=request.get_host()):  # type: ignore
        return resolve_url(settings.LOGIN_REDIRECT_URL)
    return redirect_to


@deprecate_current_app
@sensitive_post_parameters()
@csrf_protect
@never_cache
def login(
    request: HttpRequest,
    template_name: str = "frontend/registration/login.html",
    redirect_field_name: str = REDIRECT_FIELD_NAME,
    authentication_form=AuthenticationForm,
    extra_context=None,
    redirect_authenticated_user: bool = False,
) -> Union[HttpResponseRedirect, HttpResponsePermanentRedirect, TemplateResponse]:
    """Display the login form and handles the login action."""
    if extra_context is None:
        extra_context = {}
    redirect_to = request.POST.get(
        redirect_field_name, request.GET.get(redirect_field_name, "")
    )

    if redirect_authenticated_user and request.user.is_authenticated:
        redirect_to = _get_login_redirect_url(request, redirect_to)
        if redirect_to == request.path:
            raise ValueError(
                "Redirection loop for authenticated user detected. Check that "
                "your LOGIN_REDIRECT_URL doesn't point to a login page."
            )
        return HttpResponseRedirect(redirect_to)
    elif request.method == "POST":
        form = authentication_form(request, data=request.POST)

        if form.is_valid():
            auth_login(request, form.get_user())
            return redirect("frontend:machines")
        else:
            # active users without password (don't ask in ldap case)
            if settings.AUTH_ALLOW_USER_CREATION:
                try:
                    user = User.objects.get(username=request.POST["username"])
                    if user.is_active and not user.password:
                        messages.info(request, "Please receive your initial password.")
                        url = reverse("frontend:password_restore")
                        return redirect("{}?user_id={}".format(url, user.pk))
                except Exception:
                    pass
            messages.error(request, "Unknown login/password!")

            form = authentication_form(request)
    else:
        form = authentication_form(request)

    current_site = get_current_site(request)

    context = {
        "form": form,
        redirect_field_name: redirect_to,
        "site": current_site,
        "site_name": current_site.name,
        "title": "Login",
        "account_creation": settings.AUTH_ALLOW_USER_CREATION,
    }
    context.update(extra_context)

    welcome_message = ServerConfig.objects.by_key(
        "orthos.web.welcomemessage", "Come in, reserve and play..."
    )

    if welcome_message:
        messages.info(request, mark_safe(welcome_message))

    return TemplateResponse(request, template_name, context)
