from .models import Item, ContactMessage

def pending_items_count(request):
    """
    Context processor to make pending items count available to all templates.
    This is used to show notifications for admins.
    """
    if request.user.is_authenticated and request.user.is_admin_user():
        pending_count = Item.objects.filter(status='pending').count()
    else:
        pending_count = 0
    
    return {
        'pending_count': pending_count
    }

def unread_messages(request):
    """
    Context processor to make unread messages count available to all templates.
    This is used to show notification badges for user messages.
    """
    if request.user.is_authenticated:
        unread_count = ContactMessage.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
    else:
        unread_count = 0
    
    return {
        'unread_messages_count': unread_count
    }
