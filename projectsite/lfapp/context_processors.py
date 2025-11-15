from .models import ContactMessage

def unread_messages(request):
    """Add unread message count to template context"""
    if request.user.is_authenticated:
        unread_count = ContactMessage.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
        return {'unread_messages_count': unread_count}
    return {'unread_messages_count': 0}
