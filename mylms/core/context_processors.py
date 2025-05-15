from django.conf import settings
from notifications.models import Notification

def site_settings(request):
    """Adds site-wide settings to all template contexts"""
    context = {
        'site_name': 'LMS Portal',
        'site_description': 'Learning Management System',
    }
    
    # Add unread notifications count for authenticated users
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(
            user=request.user, 
            is_read=False
        ).count()
        context['unread_notifications_count'] = unread_count
    
    return context