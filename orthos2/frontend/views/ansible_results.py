"""
All views related to Ansible scan results.
"""

import logging
from typing import Any, Dict, Union

from django.contrib import messages
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import AnonymousUser
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import QuerySet
from django.http import (
    Http404,
    HttpRequest,
    HttpResponse,
    HttpResponseBase,
    HttpResponseRedirect,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import ListView

from orthos2.data.models import AnsibleScanResult, Machine

logger = logging.getLogger("views")


def is_superuser(user: Union[AbstractBaseUser, AnonymousUser]) -> bool:
    """Check if user is superuser."""
    # Typing and docs are conflicting. Let's trust the docs that this method receives a real or an anonymous user.
    # Docs: https://docs.djangoproject.com/en/4.2/topics/auth/default/#:~:text=user_passes_test
    return user.is_superuser  # type: ignore


class AnsibleResultListView(ListView):  # type: ignore
    """List view for all Ansible scan results (superuser only)."""

    model = AnsibleScanResult
    template_name = "frontend/ansible_results/list.html"
    paginate_by = 50
    context_object_name = "results"

    @method_decorator(login_required)
    @method_decorator(user_passes_test(is_superuser))
    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[AnsibleScanResult]:
        """Return filtered queryset based on query parameters."""
        queryset = AnsibleScanResult.objects.select_related("machine").all()

        # Filter by machine if specified
        machine_id = self.request.GET.get("machine_id")
        if machine_id:
            queryset = queryset.filter(machine_id=machine_id)

        # Filter by date range if specified
        date_from = self.request.GET.get("date_from")
        if date_from:
            queryset = queryset.filter(run_date__gte=date_from)

        date_to = self.request.GET.get("date_to")
        if date_to:
            queryset = queryset.filter(run_date__lte=date_to)

        # Search by machine FQDN
        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(machine__fqdn__icontains=search)

        # Order by run_date descending (most recent first)
        queryset = queryset.order_by("-run_date")

        return queryset

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Ansible Scan Results"

        # Preserve filter parameters in context for pagination links
        context["search"] = self.request.GET.get("search", "")
        context["machine_id"] = self.request.GET.get("machine_id", "")
        context["date_from"] = self.request.GET.get("date_from", "")
        context["date_to"] = self.request.GET.get("date_to", "")

        return context


@login_required
@user_passes_test(is_superuser)
def ansible_result_detail(request: HttpRequest, pk: int) -> HttpResponse:
    """Detail view for a single Ansible scan result."""
    result = get_object_or_404(
        AnsibleScanResult.objects.select_related("machine"), pk=pk
    )

    return render(
        request,
        "frontend/ansible_results/detail.html",
        {"result": result, "title": "Ansible Scan Result Detail"},
    )


@login_required
@user_passes_test(is_superuser)
@require_POST
def ansible_result_delete(request: HttpRequest, pk: int) -> HttpResponseRedirect:
    """Delete a single Ansible scan result."""
    result = get_object_or_404(AnsibleScanResult, pk=pk)
    machine_fqdn = result.machine.fqdn if result.machine else "unknown"

    result.delete()

    messages.success(
        request, f"Ansible scan result for {machine_fqdn} deleted successfully."
    )

    # Redirect back to list or machine ansible tab
    redirect_to = request.POST.get("redirect_to", "list")
    if redirect_to == "machine" and result.machine:
        return redirect("frontend:machine_ansible_results", id=result.machine.pk)
    else:
        return redirect("frontend:ansible_results_list")


@login_required
@user_passes_test(is_superuser)
@require_POST
def ansible_result_bulk_delete(request: HttpRequest) -> HttpResponseRedirect:
    """Bulk delete Ansible scan results."""
    result_ids = request.POST.getlist("result_ids")

    if not result_ids:
        messages.warning(request, "No results selected for deletion.")
        return redirect("frontend:ansible_results_list")

    count = AnsibleScanResult.objects.filter(pk__in=result_ids).delete()[0]

    messages.success(request, f"{count} Ansible scan result(s) deleted successfully.")

    return redirect("frontend:ansible_results_list")


@login_required
@user_passes_test(is_superuser)
@require_POST
def ansible_result_apply(request: HttpRequest, pk: int) -> HttpResponseRedirect:
    """Apply an Ansible scan result to its linked machine."""
    result = get_object_or_404(AnsibleScanResult, pk=pk)

    if not result.machine:
        messages.error(request, "No machine linked to this scan result.")
        return redirect("frontend:ansible_result_detail", pk=pk)

    try:
        result.apply_to_machine()
        messages.success(
            request,
            f"Ansible scan result applied to {result.machine.fqdn} successfully.",
        )
    except Exception as e:
        logger.exception(e)
        messages.error(request, f"Failed to apply scan result: {e}")

    # Redirect back to detail or machine page
    redirect_to = request.POST.get("redirect_to", "detail")
    if redirect_to == "machine" and result.machine:
        return redirect("frontend:machine_ansible_results", id=result.machine.pk)
    else:
        return redirect("frontend:ansible_result_detail", pk=pk)


@login_required
def machine_ansible_results(request: HttpRequest, id: int) -> HttpResponse:
    """Show Ansible scan results for a specific machine (tab in machine detail)."""
    try:
        machine = Machine.objects.get(pk=id)
    except Machine.DoesNotExist:
        raise Http404("Machine does not exist")

    # Get all scan results for this machine
    results = machine.ansible_scan_results.all().order_by("-run_date")

    # Paginate results
    paginator = Paginator(results, 20)
    page = request.GET.get("page", 1)

    try:
        results_page = paginator.page(page)
    except PageNotAnInteger:
        results_page = paginator.page(1)
    except EmptyPage:
        results_page = paginator.page(paginator.num_pages)

    return render(
        request,
        "frontend/machines/detail/ansible_results.html",
        {
            "machine": machine,
            "results": results_page,
            "title": "Ansible Results",
        },
    )
