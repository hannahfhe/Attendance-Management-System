# ===============================================
# leave_management/templatetags/leave_filters.py
# Create this file: leave_management/templatetags/leave_filters.py
# ===============================================

from django import template

register = template.Library()

@register.filter
def count_by_status(requests, status):
    """Count requests by status"""
    if not requests:
        return 0
    return sum(1 for request in requests if request.status == status)

@register.filter
def get_user_display_name(user):
    """Get user display name in order of preference"""
    if hasattr(user, 'full_name') and user.full_name:
        return user.full_name
    elif hasattr(user, 'get_full_name'):
        full_name = user.get_full_name()
        if full_name.strip():
            return full_name
    elif hasattr(user, 'first_name') and hasattr(user, 'last_name'):
        if user.first_name and user.last_name:
            return f"{user.first_name} {user.last_name}"
        elif user.first_name:
            return user.first_name
    return user.username

@register.filter
def get_user_initials(user):
    """Get user initials"""
    display_name = get_user_display_name(user)
    if ' ' in display_name:
        parts = display_name.split()
        return f"{parts[0][0]}{parts[-1][0]}".upper()
    return display_name[0].upper() if display_name else 'U'