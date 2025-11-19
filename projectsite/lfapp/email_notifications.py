"""
Email notification utilities for item status changes.
Sends automated emails when items are posted, approved, or rejected.
"""

from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse


def send_item_pending_email(item, request=None):
    """
    Send email notification when an item is posted and pending approval.
    
    Args
        item: Item instance that was just created
    """
    user = item.posted_by
    user_name = user.get_full_name() or user.email
    
    subject = f"Your {item.get_item_type_display()} is pending for approval - PalSU HanApp"
    
    # Determine location and date based on item type
    if item.item_type == 'lost':
        location = item.location_lost
        date = item.date_lost.strftime("%B %d, %Y") if item.date_lost else "Not specified"
    else:
        location = item.location_found
        date = item.date_found.strftime("%B %d, %Y") if item.date_found else "Not specified"
    
    message = f"""Hello {user_name},

Thank you for posting your {item.get_item_type_display()} "{item.title}" on PalSU HanApp!

Your item has been submitted and is currently pending for approval. You will receive another email once it has been reviewed.

Item Details:
- Title: {item.title}
- Category: {item.get_category_display()}
- Location: {location}
- Date: {date}


Thank you for using PalSU HanApp

---
This is an automated message from PalSU HanApp Lost and Found System
"""
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        print(f"✅ Pending approval email sent to {user.email} for item: {item.title}")
    except Exception as e:
        print(f"❌ Failed to send pending email to {user.email}: {e}")


def send_item_approved_email(item, request=None):
    """
    Send email notification when an item is approved by admin.
    
    Args
        item: Item instance that was approved
    """
    user = item.posted_by
    user_name = user.get_full_name() or user.email
    
    subject = f"✅ Your {item.get_item_type_display()} has been approved! - PalSU HanApp"
    
    # Build item URL
    if item.item_type == 'lost':
        item_path = reverse('lost_items')
    else:
        item_path = reverse('found_items')
    
    if request:
        item_url = request.build_absolute_uri(item_path)
    else:
        item_url = f"http://127.0.0.1:8000{item_path}"
    
    message = f"""Hello {user_name},

Great news! Your {item.get_item_type_display()} "{item.title}" has been approved and is now visible to everyone on PalSU HanApp.

Your item is now live and other users can see your post and contact you if they have information about your item.

View your item: {item_url}

What happens next?
- Your post is now publicly visible to all PalSU users
- Interested users can contact you through the app
- You'll receive email notifications when someone messages you
- You can edit or manage your post anytime from your dashboard

Thank you for using PalSU HanApp - together we're helping PalSUans reunite with their belongings!

---
This is an automated message from PalSU HanApp Lost and Found System
"""
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        print(f"✅ Approval email sent to {user.email} for item: {item.title}")
    except Exception as e:
        print(f"❌ Failed to send approval email to {user.email}: {e}")


def send_item_rejected_email(item, request=None):
    """
    Send email notification when an item is rejected by admin.
    
    Args:
        item: Item instance that was rejected
    """
    user = item.posted_by
    user_name = user.get_full_name() or user.email
    
    subject = f"Your {item.get_item_type_display()} submission - PalSU HanApp"
    
    message = f"""Hello {user_name},

We've reviewed your {item.get_item_type_display()} "{item.title}" and unfortunately it does not meet our posting guidelines at this time.

Common reasons for rejection:
- Insufficient or unclear description
- Inappropriate content
- Duplicate posting
- Missing required information
- Item does not belong to PSU community

What you can do:
- Review our posting guidelines
- Submit a new post with more detailed information
- Contact our admin team if you have questions

If you believe this was a mistake or have questions about this decision, please contact our admin team at palsuhanapp@gmail.com

Thank you for your understanding and for using PalSU HanApp.

---
This is an automated message from PalSU HanApp Lost and Found System
"""
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        print(f"✅ Rejection email sent to {user.email} for item: {item.title}")
    except Exception as e:
        print(f"❌ Failed to send rejection email to {user.email}: {e}")
