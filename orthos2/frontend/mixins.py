"""
Shared mixins for Orthos2 frontend views.
"""

from django.contrib.auth.mixins import UserPassesTestMixin


class SuperuserRequiredMixin(UserPassesTestMixin):
    """
    Restrict a view to superusers only.

    Unauthenticated users are redirected to the login page; authenticated
    non-superusers get a 403 (`PermissionDenied`) via `UserPassesTestMixin`'s
    default `handle_no_permission` behavior.
    """

    def test_func(self) -> bool:
        return bool(self.request.user.is_superuser)  # type: ignore[attr-defined]
