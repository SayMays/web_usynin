from django import template
from urllib.parse import urlencode
from django.http import QueryDict

register = template.Library()

@register.simple_tag
def query_string(request):
    query_dict = request.GET.copy()
    if 'page' in query_dict:
        del query_dict['page']
    return query_dict.urlencode()