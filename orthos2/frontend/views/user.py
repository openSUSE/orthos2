"""
All views for "/user"
"""

import secrets
import string
from typing import Union

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponsePermanentRedirect,
    HttpResponseRedirect,
)
from django.shortcuts import redirect, render
from rest_framework.authtoken.models import Token

from orthos2.frontend.forms.newuser import NewUserForm
from orthos2.frontend.forms.passwordrestore import PasswordRestoreForm
from orthos2.frontend.forms.preferences import PreferencesForm
from orthos2.taskmanager import tasks
from orthos2.taskmanager.models import TaskManager


def users_create(
    request: HttpRequest,
) -> Union[HttpResponsePermanentRedirect, HttpResponseRedirect, HttpResponse]:
    if request.method == "GET":
        form = NewUserForm()
    else:
        form = NewUserForm(request.POST)
        if settings.AUTH_ALLOW_USER_CREATION:
            if form.is_valid():
                username = form.cleaned_data["login"]
                email = form.cleaned_data["email"]
                password = form.cleaned_data["password"]

                new_user = User.objects.create_user(
                    username=username, email=email.lower(), password=password
                )
                new_user.save()

                new_user = authenticate(username=username, password=password)  # type: ignore
                auth_login(request, new_user)

                return redirect("frontend:machines")
        else:
            messages.error(request, "Account creation is disabled!")

    return render(
        request,
        "frontend/registration/new.html",
        {
            "form": form,
            "title": "Create User",
            "account_creation": settings.AUTH_ALLOW_USER_CREATION,
        },
    )


def users_password_restore(
    request: HttpRequest,
) -> Union[HttpResponsePermanentRedirect, HttpResponseRedirect, HttpResponse]:
    if request.method == "GET":
        user_id = request.GET.get("user_id", None)
        username = None

        if user_id is not None:
            try:
                user = User.objects.get(pk=user_id)
                username = user.username
            except Exception:
                pass

        form = PasswordRestoreForm(username=username)

    else:
        form = PasswordRestoreForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data["email"].lower()
            username = form.cleaned_data["login"]

            try:
                user = User.objects.get(email=email, username=username)
            except User.DoesNotExist:
                messages.error(request, "E-Mail/login does not exist.")
                return redirect("frontend:password_restore")

            alphabet = string.ascii_letters + string.digits
            password = "".join(secrets.choice(alphabet) for i in range(10))
            user.set_password(password)
            user.save()

            task = tasks.SendRestoredPassword(user.id, password)
            TaskManager.add(task)

            # check for multiple accounts from deprecated Orthos
            task = tasks.CheckMultipleAccounts(user.id)  # type: ignore
            TaskManager.add(task)

            messages.success(request, "Password restored - check your mails.")
            return redirect("frontend:login")

    return render(
        request,
        "frontend/registration/password_reset.html",
        {"form": form, "title": "Reset Password"},
    )


@login_required
def users_preferences(
    request: HttpRequest,
) -> Union[HttpResponsePermanentRedirect, HttpResponseRedirect, HttpResponse]:
    if request.method == "GET":
        if request.GET.get("action") == "generate_token":
            user_obj = User.objects.get(pk=request.user.id)  # type: ignore
            try:
                token = Token.objects.get(user=user_obj)  # type: ignore
                if token:
                    token.delete()
            except Token.DoesNotExist:
                pass
            token = Token.objects.create(user=user_obj)  # type: ignore
        form = PreferencesForm()
    else:
        form = PreferencesForm(request.POST)

        if form.is_valid():
            try:
                user_obj = User.objects.get(pk=request.user.id)  # type: ignore
            except User.DoesNotExist:
                messages.error(request, "User does not exist.")
                return redirect("frontend:password_restore")

            new_password = form.cleaned_data["new_password"]
            old_password = form.cleaned_data["old_password"]

            if not user_obj.check_password(old_password):
                messages.error(request, "Current password is wrong.")
                return redirect("frontend:preferences_user")

            user_obj.set_password(new_password)
            user_obj.save()

            authenticated_user = authenticate(
                username=request.user.username, password=new_password
            )

            if authenticated_user is not None:
                update_session_auth_hash(request, authenticated_user)
                messages.success(request, "Password successfully changed.")
                return redirect("frontend:preferences_user")
            else:
                messages.error(request, "Something went wrong.")
                return redirect("frontend:login")

    return render(
        request,
        "frontend/registration/preferences.html",
        {
            "form": form,
            "title": "Preferences",
            "account_creation": settings.AUTH_ALLOW_USER_CREATION,
        },
    )
