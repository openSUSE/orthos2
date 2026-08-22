"""
All views that are under "/users" and "/user/<id>/".
"""

from typing import Any, Dict, List, Union

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db.models import Q, QuerySet
from django.http import (
    Http404,
    HttpRequest,
    HttpResponse,
    HttpResponseBase,
    HttpResponseRedirect,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from rest_framework.authtoken.models import Token

from orthos2.data.models import Machine
from orthos2.frontend.forms.reservemachine import ReserveMachineForUserForm
from orthos2.frontend.forms.useradmin import UserAdminForm
from orthos2.frontend.mixins import SuperuserRequiredMixin
from orthos2.frontend.views.user import reset_and_notify_password


class UserListView(ListView):  # type: ignore
    model = User
    template_name = "frontend/users/users.html"
    paginate_by = 50

    @method_decorator(login_required)
    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        if not request.user.is_superuser:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[User]:
        filters: List[Q] = []

        query = self.request.GET.get("query")
        if query:
            filters.append(
                Q(username__icontains=query)
                | Q(email__icontains=query)
                | Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
            )

        is_staff = self.request.GET.get("is_staff")
        if is_staff == "1":
            filters.append(Q(is_staff=True))
        elif is_staff == "0":
            filters.append(Q(is_staff=False))

        is_superuser = self.request.GET.get("is_superuser")
        if is_superuser == "1":
            filters.append(Q(is_superuser=True))
        elif is_superuser == "0":
            filters.append(Q(is_superuser=False))

        return super().get_queryset().filter(*filters)  # type: ignore

    def get_ordering(self) -> str:
        order_by = self.request.GET.get("order_by")
        order_direction = self.request.GET.get("order_direction")

        if order_by and order_direction in {"asc", "desc"}:
            return (
                "{}".format(order_by)
                if order_direction == "desc"
                else "-{}".format(order_by)
            )
        return "username"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Users"
        return context


class NewUser(SuperuserRequiredMixin, CreateView):
    model = User
    template_name = "frontend/users/new_user.html"
    success_url = reverse_lazy("frontend:users")
    form_class = UserAdminForm

    def form_valid(self, form: UserAdminForm) -> HttpResponseRedirect:
        self.object = form.save(commit=False)
        # No password field on this form - the account starts with no usable
        # password; a superuser grants access via "Send password reset email".
        self.object.set_unusable_password()
        self.object.save()
        form.save_m2m()
        messages.success(
            self.request,
            f"User '{self.object.username}' created. "
            "Use 'Send password reset email' on their profile to grant access.",
        )
        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "New User"
        context["action"] = "new"
        return context


class UserDetailedEdit(SuperuserRequiredMixin, UpdateView):
    model = User
    template_name = "frontend/users/new_user.html"
    success_url = reverse_lazy("frontend:users")
    form_class = UserAdminForm

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit User"
        context["action"] = "edit"
        return context


class DeleteUser(SuperuserRequiredMixin, DeleteView):  # type: ignore
    model = User
    template_name = "frontend/users/user_confirm_deletion.html"
    success_url = reverse_lazy("frontend:users")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Delete User"
        return context


@login_required
def user_toggle_active(request: HttpRequest, id: int) -> HttpResponseRedirect:
    if not request.user.is_superuser:
        raise PermissionDenied
    user_obj = get_object_or_404(User, pk=id)
    if request.method == "POST":
        user_obj.is_active = not user_obj.is_active
        user_obj.save()
        state = "activated" if user_obj.is_active else "deactivated"
        messages.success(request, f"User '{user_obj.username}' {state}.")
    return redirect("frontend:user_detail", id=id)


@login_required
def user_send_password_reset(request: HttpRequest, id: int) -> HttpResponseRedirect:
    if not request.user.is_superuser:
        raise PermissionDenied
    user_obj = get_object_or_404(User, pk=id)
    if request.method == "POST":
        if user_obj.social_auth.exists():  # type: ignore[attr-defined]
            messages.error(
                request,
                f"'{user_obj.username}' logs in via OIDC - no local password to reset.",
            )
        else:
            reset_and_notify_password(user_obj)
            messages.success(
                request, f"Password reset email sent to '{user_obj.username}'."
            )
    return redirect("frontend:user_detail", id=id)


@login_required
def user_detail(request: HttpRequest, id: int) -> HttpResponse:
    if not request.user.is_superuser:
        raise PermissionDenied
    try:
        user_obj = User.objects.prefetch_related(
            "groups", "user_permissions", "social_auth"
        ).get(pk=id)
        return render(
            request,
            "frontend/users/detail/overview.html",
            {"user_obj": user_obj, "title": f"User {user_obj.username}"},
        )
    except User.DoesNotExist:
        raise Http404("User does not exist")


@login_required
def user_reservations(request: HttpRequest, id: int) -> HttpResponse:
    if not request.user.is_superuser:
        raise PermissionDenied
    try:
        user_obj = User.objects.get(pk=id)
        machines = Machine.objects.filter(reserved_by_id=id).select_related(
            "reserved_by"
        )
        return render(
            request,
            "frontend/users/detail/reservations.html",
            {
                "user_obj": user_obj,
                "machines": machines,
                "title": f"User {user_obj.username} Reservations",
            },
        )
    except User.DoesNotExist:
        raise Http404("User does not exist")


@login_required
def user_tokens(request: HttpRequest, id: int) -> HttpResponse:
    if not request.user.is_superuser:
        raise PermissionDenied
    user_obj = get_object_or_404(User, pk=id)
    tokens = Token.objects.filter(user=user_obj)
    return render(
        request,
        "frontend/users/detail/tokens.html",
        {
            "user_obj": user_obj,
            "tokens": tokens,
            "title": f"User {user_obj.username} Tokens",
        },
    )


@login_required
def user_reserve_machine(
    request: HttpRequest, id: int
) -> Union[HttpResponse, HttpResponseRedirect]:
    if not request.user.is_superuser:
        raise PermissionDenied
    user_obj = get_object_or_404(User, pk=id)

    if request.method == "POST":
        form = ReserveMachineForUserForm(request.POST)
        if form.is_valid():
            fqdn = form.cleaned_data["machine"]
            reason = form.cleaned_data["reason"]
            until = form.cleaned_data["until"]
            try:
                machine = Machine.objects.get(fqdn=fqdn)
                machine.reserve(
                    reason, until, user=request.user, reserve_for_user=user_obj
                )
                messages.success(
                    request, f"Machine '{fqdn}' reserved for {user_obj.username}."
                )
                return redirect("frontend:user_detail", id=id)
            except Machine.DoesNotExist:
                form.add_error("machine", f"Machine '{fqdn}' not found.")
            except Exception as e:
                messages.error(request, str(e))
    else:
        form = ReserveMachineForUserForm()

    return render(
        request,
        "frontend/users/reserve.html",
        {
            "form": form,
            "user_obj": user_obj,
            "title": f"Reserve Machine for {user_obj.username}",
        },
    )
