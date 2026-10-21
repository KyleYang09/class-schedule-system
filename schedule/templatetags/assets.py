import os

from django import template
from django.contrib.staticfiles import finders
from django.templatetags.static import static

register = template.Library()


@register.simple_tag
def asset(path):
    url = static(path)
    found = finders.find(path)
    if not found:
        return url
    return f'{url}?v={int(os.path.getmtime(found))}'
