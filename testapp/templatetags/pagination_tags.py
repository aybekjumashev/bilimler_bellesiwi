# testapp/templatetags/pagination_tags.py

from django import template
from django.http import QueryDict
from urllib.parse import urlencode

register = template.Library()

@register.simple_tag(takes_context=True)
def build_pagination_url(context, **kwargs):
    """
    Build pagination URL preserving current GET parameters
    Usage: {% build_pagination_url page=2 %}
    """
    request = context['request']
    get_params = request.GET.copy()
    
    # Update with new parameters
    for key, value in kwargs.items():
        if value is None:
            get_params.pop(key, None)
        else:
            get_params[key] = value
    
    # Build query string
    if get_params:
        return '?' + get_params.urlencode()
    return ''

@register.simple_tag(takes_context=True)
def pagination_url(context, page_number):
    """
    Generate pagination URL for specific page number
    Usage: {% pagination_url 2 %}
    """
    return build_pagination_url(context, page=page_number)

@register.simple_tag(takes_context=True) 
def remove_param(context, param_name):
    """
    Remove specific parameter from current URL
    Usage: {% remove_param 'page' %}
    """
    request = context['request']
    get_params = request.GET.copy()
    get_params.pop(param_name, None)
    
    if get_params:
        return '?' + get_params.urlencode()
    return ''

@register.simple_tag(takes_context=True)
def current_params(context):
    """
    Get current URL parameters as string
    Usage: {% current_params %}
    """
    request = context['request']
    return request.GET.urlencode()

@register.filter
def get_item(dictionary, key):
    """
    Get item from dictionary
    Usage: {{ mydict|get_item:"key" }}
    """
    return dictionary.get(key)

@register.inclusion_tag('testapp/includes/pagination.html', takes_context=True)
def render_pagination(context, page_obj, paginator, page_range):
    """
    Render pagination component
    Usage: {% render_pagination page_obj paginator page_range %}
    """
    return {
        'page_obj': page_obj,
        'paginator': paginator, 
        'page_range': page_range,
        'request': context['request'],
    }