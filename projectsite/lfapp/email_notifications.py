"""
Email notification utilities for item status changes.
Sends automated emails when items are posted, approved, or rejected.
"""

from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from .models import CustomUser, Item
from django.db.models import Q


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


def send_role_change_email(user, new_role, actor=None):
    """
    Send email notification when a user's role is changed.
    
    Args:
        user: User instance whose role was changed
        new_role: The new role assigned (string)
        actor: User instance who performed the action (optional)
    """
    user_name = user.get_full_name() or user.email
    actor_name = "an Admin"
    if actor:
        actor_name = actor.get_full_name() or actor.email
        
    subject = "Role Update Notification - PalSU HanApp"
    
    # Determine message based on role change
    if new_role == 'admin':
        action_msg = f"Congratulations! You have been promoted to **Admin** by {actor_name}."
        details = """As an Admin, you now have access to:
- User Management Dashboard
- Item Moderation Queue
- Ability to approve/reject items
- Ability to promote other users"""
    elif new_role == 'verified':
        if user == actor:
            action_msg = "You have successfully stepped down from your Admin role."
            details = "You are now a Verified User. You can still post items but no longer have admin privileges."
        else:
            action_msg = f"Your role has been updated to **Verified User** by {actor_name}."
            details = "You can still post items, but admin privileges have been revoked."
    else: # public
        action_msg = f"Your role has been updated to **Public User** by {actor_name}."
        details = "You can browse items but can no longer post new items until you are verified again."

    message = f"""Hello {user_name},

{action_msg}

{details}

If you believe this change was made in error, please contact the system administrator.

Thank you for using PalSU HanApp.

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
        print(f"✅ Role change email sent to {user.email} (New Role: {new_role})")
    except Exception as e:
        print(f"❌ Failed to send role change email to {user.email}: {e}")


def send_admin_new_item_notification(item):
    """
    Send email notification to all admins when a new item is posted.
    
    Args:
        item: Item instance that was posted
    """
    from .models import CustomUser
    from django.db.models import Q
    
    # Get all admins and superusers
    admins = CustomUser.objects.filter(Q(role='admin') | Q(is_superuser=True)).distinct()
    recipient_list = [admin.email for admin in admins if admin.email]
    
    if not recipient_list:
        print("⚠️ No admins found to notify.")
        return

    subject = f"New Item Pending Review: {item.title} - PalSU HanApp"
    
    # Build admin URL (assuming standard admin path or custom dashboard)
    # Change if deployed or add if DEBUG local else deployed host
    admin_url = "http://127.0.0.1:8000/dashboard/moderation/" 
    
    message = f"""Hello Admin,

A new item has been posted and is waiting for review.

Item Details:
- Title: {item.title}
- Type: {item.get_item_type_display()}
- Category: {item.get_category_display()}
- Posted By: {item.posted_by.get_full_name() or item.posted_by.email}
- Date: {item.created_at.strftime("%B %d, %Y %I:%M %p")}

Please review this item in the moderation queue:
{admin_url}

---
This is an automated message from PalSU HanApp Lost and Found System
"""
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=False,
        )
        print(f"✅ Admin notification sent to {len(recipient_list)} admins for item: {item.title}")
    except Exception as e:
        print(f"❌ Failed to send admin notification: {e}")


def send_item_archived_email(item, archived_by, reason, notes=''):
    """
    Send email notif when admin delete/archive an item
    """
    user = item.posted_by
    user_name = user.get_full_name() or user.email
    admin_name = archived_by.get_full_name() or archived_by.email
    
    
    reason_display = {
        'spam': 'Spam',
        'inappropriate': 'Inappropriate content',
        'duplicate': 'Duplicate post',
        'resolved': 'Resolved / No longer needed',
        'other': 'Other'
    }.get(reason, reason)
    
    subject = f"Your item has been removed - PalSU HanApp"
    
    # Itep type
    if item.item_type == 'lost':
        location = item.location_lost
    else:
        location = item.location_found
    
    # Notes section if provided
    notes_section = ""
    if notes:
        notes_section = f"""
Additional Notes from Admin:
{notes}
"""
    
    message = f"""Hello {user_name},

We are writing to inform you that your item posting has been removed from PalSU HanApp.

Item Details:
- Title: {item.title}
- Type: {item.get_item_type_display()}
- Category: {item.get_category_display()}
- Location: {location}

Removal Details:
- Reason: {reason_display}
- Removed by Admin: {admin_name}
- Date: {item.archived_at.strftime("%B %d, %Y at %I:%M %p")}
{notes_section}
If you believe this was done in error or have any questions, please contact the system administrator.

Thank you for your understanding.

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
        print(f"✅ Archive notification email sent to {user.email} for item: {item.title}")
    except Exception as e:
        print(f"❌ Failed to send archive notification to {user.email}: {e}")


def send_admin_item_updated_notification(item, old_values):
    
    # Send email notification to all admins when an item is updated by its poster.
    # Get admins
    admins = CustomUser.objects.filter(Q(role='admin') | Q(is_superuser=True)).distinct()
    recipient_list = [admin.email for admin in admins if admin.email]
    
    if not recipient_list:
        print("⚠️ No admins found to notify.")
        return

    subject = f"Item Updated - Pending Re-approval: {item.title} - PalSU HanApp"
    
    # For comparison of changes
    admin_url = "http://127.0.0.1:8000/dashboard/moderation/"
    
    # Original POST
    old_category = dict(Item.CATEGORY_CHOICES).get(old_values.get('category'), old_values.get('category'))
    
    if item.item_type == 'lost':
        old_location_label = "Location Lost"
        old_location_value = old_values.get('location_lost', 'Not specified')
        old_date_label = "Date Lost"
        old_date_value = old_values.get('date_lost').strftime("%B %d, %Y") if old_values.get('date_lost') else "Not specified"
        
        new_location_label = "Location Lost"
        new_location_value = item.location_lost or 'Not specified'
        new_date_label = "Date Lost"
        new_date_value = item.date_lost.strftime("%B %d, %Y") if item.date_lost else "Not specified"
    else:
        old_location_label = "Location Found"
        old_location_value = old_values.get('location_found', 'Not specified')
        old_date_label = "Date Found"
        old_date_value = old_values.get('date_found').strftime("%B %d, %Y") if old_values.get('date_found') else "Not specified"
        
        new_location_label = "Location Found"
        new_location_value = item.location_found or 'Not specified'
        new_date_label = "Date Found"
        new_date_value = item.date_found.strftime("%B %d, %Y") if item.date_found else "Not specified"
    
    # Check if image was changed
    image_changed = old_values.get('image') != (item.image.name if item.image else '')
    image_note = "\n\n📷 Note: The item image was also changed." if image_changed else ""
    
    message = f"""Hello Admin,

An existing item has been updated by its poster and requires re-approval.

Item Information:
- Item ID: #{item.id}
- Posted By: {item.posted_by.get_full_name() or item.posted_by.email}
- Original Post Date: {item.created_at.strftime("%B %d, %Y")}
- Updated: {item.content_updated_at.strftime("%B %d, %Y at %I:%M %p") if item.content_updated_at else 'Just now'}

=== ORIGINAL POST ===
Title: {old_values.get('title', '')}
Description: {old_values.get('description', '')}
Category: {old_category}
{old_location_label}: {old_location_value}
{old_date_label}: {old_date_value}
Contact Number: {old_values.get('contact_number') or 'Not provided'}
Display Name: {'Yes' if old_values.get('display_name') else 'No'}

=== UPDATED POST ===
Title: {item.title}
Description: {item.description}
Category: {item.get_category_display()}
{new_location_label}: {new_location_value}
{new_date_label}: {new_date_value}
Contact Number: {item.contact_number or 'Not provided'}
Display Name: {'Yes' if item.display_name else 'No'}{image_note}

Please review this updated item in the moderation queue:
{admin_url}

---
This is an automated message from PalSU HanApp Lost and Found System
"""
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=False,
        )
        print(f"✅ Admin update notification sent to {len(recipient_list)} admins for item: {item.title}")
    except Exception as e:
        print(f"❌ Failed to send admin update notification: {e}")

