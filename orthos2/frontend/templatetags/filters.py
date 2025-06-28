import re
from typing import TYPE_CHECKING, Dict, Optional

from django import template
from django.templatetags.static import static
from django.utils.html import escape
from django.utils.safestring import SafeString, mark_safe

if TYPE_CHECKING:
    from orthos2.data.models.netboxorthoscomparision import NetboxOrthosComparisionRun

register = template.Library()


@register.filter
def divide(value: float, arg: int) -> Optional[str]:
    """Divide ``value`` and return float value rounded to one decimal place."""
    try:
        return format(float(value) / arg, ".1f")
    except (ValueError, ZeroDivisionError):
        return None


@register.filter
def boolean_image(value: bool, size: int = 25) -> str:
    """Return an HTML image tag with ``size`` (width in px) if ``value`` is true."""
    if value:
        return "&#9989;"
    else:
        return "&#10005;"


@register.filter
def vendor_image(cpu_model: str, size: int = 25) -> SafeString:
    """Return an HTML image tag with ``size`` (width in px) and the repective vendor logo."""
    cpu_model = cpu_model.lower()

    img = '<img src="{{}}" width="{}px"/>'.format(size)

    if "intel" in cpu_model:
        return mark_safe(img.format(static("frontend/images/intel.png")))

    if "amd" in cpu_model:
        return mark_safe(img.format(static("frontend/images/amd.png")))

    if "power" in cpu_model:
        return mark_safe(img.format(static("frontend/images/ibm.png")))

    return mark_safe('<i class="fa fa-question"></i>')


@register.filter
def pcihooks(lspci: str) -> SafeString:
    """
    Escapes the lspci string and set HTML hooks for every PCI slot ID.

    Example:
        "00:00.0 ..." > "<a href="#00:00.0">00:00.0</a> ..."
    """
    result = re.sub(
        r"([a-fA-F0-9]+:[a-fA-F0-9]+.[a-fA-F0-9]+) (.*)",
        r'<a name="\1" class="monospace">\1</a> \2',
        str(escape(lspci)),
    )
    return mark_safe(result)


@register.filter
def get_netbox_comparison_result(
    comparison_results: Dict[str, "NetboxOrthosComparisionRun"], interface_name: str
) -> Optional["NetboxOrthosComparisionRun"]:
    """
    Get the NetBox comparison result for a specific interface name.

    Args:
        comparison_results: The comparison results dictionary.
        interface_name: The name of the interface to look for.

    Returns:
        The comparison result for the specified interface, or None if not found.
    """
    return comparison_results.get(interface_name, None)
