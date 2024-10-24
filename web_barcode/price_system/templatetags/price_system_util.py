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


@register.filter
def round_number_two(value):
    return round(value, 2)


@register.filter
def float_number_filter(value):
    return float(value)


@register.filter
def float_for_js(value):
    return str(value).replace(',', '.')

@register.filter
def short_text(value, short_int):
    return value[:short_int]
