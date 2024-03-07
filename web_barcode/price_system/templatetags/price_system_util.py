from django import template

register = template.Library()


@register.filter
def get_type(value):
    return type(value)


@register.filter
def integer(value):
    return int(value)


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)
