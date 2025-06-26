from django import template
from django.template.defaultfilters import slugify

register = template.Library()

@register.filter
def get_item(obj, key):
    """Get an item from a dictionary or list safely."""
    if isinstance(obj, dict):
        return obj.get(key, None)
    elif isinstance(obj, (list, tuple)) and isinstance(key, int) and 0 <= key < len(obj):
        return obj[key]
    return None

@register.filter
def get_display_value(result, field_info):
    """Get the display value for a field, using formatted version if available."""
    if isinstance(field_info, dict):
        field = field_info.get('field', '')
        actual_field = field_info.get('actual_field', field)
    else:
        field = field_info
        actual_field = field
    
    # Check if this is a date field with a display value
    if '__' in actual_field:
        display_key = f"{actual_field}_display"
        if display_key in result:
            return result[display_key]
    
    # Otherwise return the regular value
    return result.get(actual_field)

@register.filter
def get_display(value, model_opts):
    """Get the display value for a field choice."""
    if value is None:
        return None
    
    # Create a dict of field choices for efficient lookup
    # We use a string comparison for values to handle different types
    str_value = str(value)
    
    # Search only through fields that have choices
    for field in model_opts.fields:
        if hasattr(field, 'choices') and field.choices:
            for choice_value, choice_display in field.choices:
                if str(choice_value) == str_value:
                    return choice_display
    
    return value