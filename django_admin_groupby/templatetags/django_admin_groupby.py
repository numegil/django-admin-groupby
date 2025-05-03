from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary safely."""
    return dictionary.get(key, None)

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