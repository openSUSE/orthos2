"""
All views that are under "/users" and "/user/<id>/".
"""

from typing import Any, Dict, List

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db.models import Q, QuerySet
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseBase
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import ListView

from orthos2.data.models import Machine


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
