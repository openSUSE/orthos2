"""
All views that are under "/tokens".
"""

from typing import Any, Dict, Optional

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import DeleteView, ListView
from rest_framework.authtoken.models import Token

from orthos2.frontend.mixins import SuperuserRequiredMixin


class TokenListView(SuperuserRequiredMixin, ListView):  # type: ignore
    model = Token
    template_name = "frontend/tokens/tokens.html"
    paginate_by = 50

    def get_queryset(self) -> "QuerySet[Token]":
        return (
            super()
            .get_queryset()
            .select_related("user")  # type: ignore[attr-defined]
            .order_by("user__username")
        )

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Tokens"
        return context


class DeleteToken(SuperuserRequiredMixin, DeleteView):  # type: ignore
    """
    Keyed on the owning user's id, not the token's key, so the secret key
    never ends up in a URL (browser history, server access logs, referers).
    """

    model = Token
    template_name = "frontend/tokens/token_confirm_deletion.html"
    success_url = reverse_lazy("frontend:tokens")

    def get_object(self, queryset: Optional["QuerySet[Token]"] = None) -> Token:
        return get_object_or_404(Token, user_id=self.kwargs["user_id"])

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Revoke Token"
        return context
