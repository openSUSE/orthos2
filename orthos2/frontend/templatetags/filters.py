import re

from django import template
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.utils.html import escape, mark_safe

from data.models import Machine

register = template.Library()


@register.filter
def divide(value, arg):
    """Divide ``value`` and return float value rounded to one decimal place."""
    try:
        return format(float(value) / arg, '.1f')
    except (ValueError, ZeroDivisionError):
        return None


@register.filter
def boolean_image(value, size=25):
    """Return an HTML image tag with ``size`` (width in px) if ``value`` is true."""
    if value:
        return '&#9989;'
    else:
        return '&#10005;'


@register.filter
def vendor_image(cpu_model, size=25):
    """Return an HTML image tag with ``size`` (width in px) and the repective vendor logo."""
    cpu_model = cpu_model.lower()

    img = '<img src="{{}}" width="{}px"/>'.format(size)

    if 'intel' in cpu_model:
        return mark_safe(img.format(static('frontend/images/intel.png')))

    if 'amd' in cpu_model:
        return mark_safe(img.format(static('frontend/images/amd.png')))

    if 'power' in cpu_model:
        return mark_safe(img.format(static('frontend/images/ibm.png')))

    return mark_safe('<i class="fa fa-question"></i>')


@register.filter
def pcihooks(lspci):
    """
    Escapes the lspci string and set HTML hooks for every PCI slot ID.

    Example:
        "00:00.0 ..." > "<a href="#00:00.0">00:00.0</a> ..."
    """
    result = escape(lspci)
    result = re.sub(
        r'([a-fA-F0-9]+:[a-fA-F0-9]+.[a-fA-F0-9]+) (.*)',
        r'<a name="\1" class="monospace">\1</a> \2',
        result
    )
    return mark_safe(result)
