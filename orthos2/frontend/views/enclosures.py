"""
All views that are under "/machines".
"""

from typing import Any, Dict, List

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import AnonymousUser
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q, QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseBase
from django.shortcuts import redirect, render  # type: ignore
from django.utils.decorators import method_decorator  # type: ignore
from django.views.generic import ListView, DetailView

from orthos2.data.models import Enclosure

class EnclosureListView(ListView):
    model = Enclosure

    template_name = "frontend/enclosures/enclosures.html"
    def get_queryset(self) -> QuerySet["Enclosure"]:
        enclosures = super(EnclosureListView, self).get_queryset()
        return enclosures.all()

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)  # type: ignore
        context["enclosure_list"] = self.object_list # type: ignore
        return context

class EnclosureDetailed(DetailView):
    model = Enclosure
