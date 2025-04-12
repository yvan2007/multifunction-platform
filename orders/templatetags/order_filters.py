# orders/templatetags/order_filters.py
from django import template

register = template.Library()

@register.filter
def in_list(value, arg):
    """Check if a value is in a comma-separated list."""
    return value in arg.split(',')