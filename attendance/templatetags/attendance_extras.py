from django import template

register = template.Library()

@register.filter
def lookup(dictionary, key):
    """Template filter to lookup dictionary values by key"""
    if dictionary and key in dictionary:
        return dictionary[key]
    return None

@register.filter
def get_item(dictionary, key):
    """Alternative template filter to get dictionary items"""
    return dictionary.get(key)
