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
    # print('dictionary', dictionary, key)
    return dictionary.get(key)


@register.filter
def list_position(list_data, arg):
    return list_data[arg]


@register.filter
def multiplicity(value, arg):
    return value * arg


@register.filter
def divide(value, arg):
    return value / arg


@register.filter
def sub(value, arg):
    return value - arg


@register.filter
def add(value, arg):
    return value + arg


@register.filter
def round_number(value):
    return round(value)
