from django import template

register = template.Library()

@register.filter
def format_display_name(user):
    """
    Format user's display name as 'FirstName L.' where L is the first letter of the last name.
    Falls back to username if full name is not available.
    """
    full_name = user.get_full_name()
    
    if full_name:
        # Split the full name into parts
        name_parts = full_name.strip().split()
        
        if len(name_parts) >= 2:
            # First name + last name initial with dot
            first_name = name_parts[0]
            last_initial = name_parts[-1][0].upper()
            return f"{first_name} {last_initial}."
        else:
            # Only one name part, return as is
            return full_name
    else:
        # No full name, return username
        return user.username
