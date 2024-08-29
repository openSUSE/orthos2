from typing import Any, Optional

from django import template
from django.http import HttpRequest
from django.urls import resolve, reverse
from django.utils.safestring import SafeString, mark_safe

from orthos2.data.models import Machine, ServerConfig

register = template.Library()


# from: http://stackoverflow.com/questions/2047622/how-to-paginate-django-with-other-get-variables
@register.simple_tag
def url_replace(
    request: HttpRequest, field: str, value: Any, remove: bool = False
) -> str:
    """
    Replace ``field`` by value in GET parameters.

    If ``remove`` is True, the field gets removed.
    If a filter option gets selected, the page for the paginator needs to be set to 1 due to a
    different (less) search result list.
    """
    params = request.GET.copy()
    if field != "page":
        if "page" in params:
            params["page"] = "1"

    if remove and (field in params):
        del params[field]
    else:
        params[field] = value

    return params.urlencode()


@register.simple_tag
def active(request: HttpRequest, name: str) -> Optional[str]:
    """Return 'active' if ``name`` is in GET parameters."""
    return "active" if name in list(request.GET.values()) else None


@register.simple_tag
def active_view(request: HttpRequest, view: str) -> Optional[str]:
    """Return 'active' if ``view`` gets requested."""
    return "active" if view == resolve(request.path_info).url_name else None


@register.simple_tag
def disabled(request: HttpRequest, name: str) -> Optional[str]:
    """Return 'disabled' if ``name`` is in GET parameters."""
    return "disabled" if name in list(request.GET.values()) else None


@register.simple_tag
def get_bugreport_url() -> str:
    """Return bugreport URL for templates."""
    url = ServerConfig.objects.by_key("orthos.bugreport.url")
    if not url:
        url = "#"
    return url


@register.simple_tag
def get_documentation_url() -> str:
    """Return documentation URL for templates."""
    url = ServerConfig.objects.by_key("orthos.documentation.url")
    if not url:
        url = "#"
    return url


@register.simple_tag
def get_enhancement_url() -> str:
    """Return enhancement URL for emplates."""
    url = ServerConfig.objects.by_key("orthos.enhancement.url")
    if not url:
        url = "#"
    return url


@register.simple_tag
def get_current_domain_filter(request: HttpRequest) -> str:
    """Return the current domain from GET (if available)."""
    domain = request.GET.get("domain", None)
    if (not domain) or (domain == ""):
        domain = "All Network Domains"
    return domain


@register.simple_tag
def get_current_machinegroup_filter(request: HttpRequest) -> str:
    """Return the current machine group from GET (if available)."""
    group = request.GET.get("machinegroup", None)
    if (not group) or (group == ""):
        group = "All Machine Groups"
    return group


@register.simple_tag
def get_cli_url() -> str:
    """Return the URL to the Orthos command line client (CLI)."""
    url = ServerConfig.objects.by_key("orthos.cli.url")
    if not url:
        url = "#"
    return url


@register.simple_tag
def status_ipv4(machine: Machine) -> SafeString:
    if machine.check_connectivity < Machine.Connectivity.PING:
        return mark_safe(
            '<td class="blue"><span class="text-small">Disabled</span></td>'
        )

    text = dict(Machine.StatusIP.CHOICE).get(machine.status_ipv4)

    if machine.status_ipv4 == Machine.StatusIP.UNREACHABLE:
        result = '<td class="red" title="{}"><i class="fa fa-close"></i></td>'
    elif machine.status_ipv4 == Machine.StatusIP.REACHABLE:
        result = '<td class="green" title="{}">(<i class="fa fa-check"></i>)</td>'
    elif machine.status_ipv4 == Machine.StatusIP.CONFIRMED:
        result = '<td class="green" title="{}"><i class="fa fa-check"></i></td>'
    elif machine.status_ipv6 == Machine.StatusIP.AF_DISABLED:
        result = '<td class="green" title="{}"><i class="fa fa-minus-circle"></i></td>'
    else:
        result = '<td class="yellow" title="{}"><i class="fa fa-exclamation-triangle"></i></td>'

    return mark_safe(result.format(text))


@register.simple_tag
def status_ipv6(machine: Machine) -> SafeString:
    if machine.check_connectivity < Machine.Connectivity.PING:
        return mark_safe(
            '<td class="blue"><span class="text-small">Disabled</span></td>'
        )

    text = dict(Machine.StatusIP.CHOICE).get(machine.status_ipv6)

    if machine.status_ipv6 == Machine.StatusIP.UNREACHABLE:
        result = '<td class="red" title="{}"><i class="fa fa-close"></i></td>'
    elif machine.status_ipv6 == Machine.StatusIP.REACHABLE:
        result = '<td class="green" title="{}">(<i class="fa fa-check"></i>)</td>'
    elif machine.status_ipv6 == Machine.StatusIP.CONFIRMED:
        result = '<td class="green" title="{}"><i class="fa fa-check"></i></td>'
    elif machine.status_ipv6 == Machine.StatusIP.AF_DISABLED:
        result = '<td class="green" title="{}"><i class="fa fa-minus-circle"></i></td>'
    else:
        result = '<td class="yellow" title="{}"><i class="fa fa-exclamation-triangle"></i></td>'

    return mark_safe(result.format(text))


@register.simple_tag
def status_ssh(machine: Machine) -> SafeString:
    if machine.check_connectivity < Machine.Connectivity.SSH:
        return mark_safe(
            '<td class="blue"><span class="text-small">Disabled</span></td>'
        )

    if machine.status_ssh:
        result = (
            '<td class="green" title="SSH port open"><i class="fa fa-check"></i></td>'
        )
    else:
        result = (
            '<td class="red" title="SSH port not open"><i class="fa fa-close"></i></td>'
        )

    return mark_safe(result)


@register.simple_tag
def status_login(machine: Machine) -> SafeString:
    if machine.check_connectivity < Machine.Connectivity.ALL:
        return mark_safe(
            '<td class="blue"><span class="text-small">Disabled</span></td>'
        )

    if machine.status_login:
        result = '<td class="green" title="Login was successful"><i class="fa fa-check"></i></td>'
    else:
        result = '<td class="red" title="Login was not successful"><i class="fa fa-close"></i></td>'

    return mark_safe(result)


@register.simple_tag
def order_list(request: HttpRequest, field: str) -> SafeString:
    """Return ordering arrows."""
    up = '<i class="fa fa-caret-down"></i>'
    down = '<i class="fa fa-caret-up"></i>'

    params = request.GET.copy()
    params["order_by"] = field
    params["order_direction"] = "desc"
    url_asc = "{}?{}".format(request.path, params.urlencode())
    params["order_direction"] = "asc"
    url_desc = "{}?{}".format(request.path, params.urlencode())

    return mark_safe(
        '<a href="{}">{}</a><a href="{}">{}</a>'.format(url_asc, up, url_desc, down)
    )


@register.simple_tag
def vm_record(request: HttpRequest, vm: Machine) -> SafeString:
    """Return HTML table row for a single virtual machine."""
    if request.user.is_superuser or (
        request.user == vm.reserved_by
        and vm.hypervisor
        and vm.hypervisor.vm_auto_delete
    ):
        button = '<a class="btn btn-sm btn-danger" href="javascript:void(0);"'
        button += ' onClick="delete_vm({})">'.format(vm.pk)
    else:
        button = '<a class="btn btn-sm btn-danger disabled" href="#">'
    button += '<i class="fa fa-trash-o"></i> Delete</a>'

    result = "<tr>"
    result += '  <td><a href="{url}">{vm.fqdn}</a></td>'
    result += "  <td>{vm.mac_address}</td>"
    result += "  <td>{vm.reserved_by}</td>"
    result += "  {status}"
    result += "  <td>{button}</td>"
    result += "</tr>"
    result = result.format(
        url=reverse("frontend:detail", args=[vm.pk]),
        vm=vm,
        status=status_ipv4(vm) + status_ipv6(vm) + status_ssh(vm) + status_login(vm),
        button=button,
    )
    return mark_safe(result)
