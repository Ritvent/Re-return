from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.core.paginator import Paginator
from .models import Item, CustomUser
from .forms import ItemForm
from .email_notifications import send_item_pending_email, send_item_approved_email, send_item_rejected_email

def landing_view(request):
    """Landing page with login form"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        from django.contrib.auth import authenticate
        email = request.POST.get('username')  # Using username field for email
        password = request.POST.get('password')
        
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid email or password')
    
    return render(request, 'lfapp/landing.html')

def home_view(request):
    """Home page showing recent lost and found items - Public and authenticated users can view"""
    # Get recent lost items (limit to 3)
    recent_lost = Item.objects.filter(
        item_type='lost',
        status='approved',
        is_active=True
    ).select_related('posted_by').order_by('-created_at')[:3]
    
    # Get recent found items (limit to 3)
    recent_found = Item.objects.filter(
        item_type='found',
        status='approved',
        is_active=True
    ).select_related('posted_by').order_by('-created_at')[:3]
    
    # Get recent claimed/completed items (limit to 5)
    recent_claimed = Item.objects.filter(
        status__in=['claimed', 'found'],
        is_active=True
    ).select_related('posted_by', 'claimed_by').order_by('-completed_at')[:5]
    
    context = {
        'recent_lost': recent_lost,
        'recent_found': recent_found,
        'recent_claimed': recent_claimed,
    }
    
    return render(request, 'lfapp/home.html', context)

def lost_items_view(request):
    """View all lost items with search and filter - Public access allowed"""
    # Show approved items to everyone, plus pending items to their owners
    if request.user.is_authenticated:
        items = Item.objects.filter(
            item_type='lost'
        ).filter(
            Q(status='approved', is_active=True) | Q(posted_by=request.user)
        ).select_related('posted_by').order_by('-created_at')
    else:
        items = Item.objects.filter(
            item_type='lost',
            status__in=['approved']
        ).select_related('posted_by').order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        items = items.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(location_lost__icontains=search_query)
        )
    
    # Category filter
    category_filter = request.GET.get('category', '')
    if category_filter:
        items = items.filter(category=category_filter)
    
    # Get all categories for filter dropdown
    categories = Item.ITEM_TYPE_CHOICES  # This should be CATEGORY_CHOICES
    categories = Item.CATEGORY_CHOICES
    
    context = {
        'items': items,
        'categories': categories,
    }
    
    return render(request, 'lfapp/lost_items.html', context)

def found_items_view(request):
    """View all found items with search and filter - Public access allowed"""
    # Show approved items to everyone, plus pending items to their owners
    if request.user.is_authenticated:
        items = Item.objects.filter(
            item_type='found'
        ).filter(
            Q(status='approved', is_active=True) | Q(posted_by=request.user)
        ).select_related('posted_by').order_by('-created_at')
    else:
        items = Item.objects.filter(
            item_type='found',
            status__in=['approved']
        ).select_related('posted_by').order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        items = items.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(location_found__icontains=search_query)
        )
    
    # Category filter
    category_filter = request.GET.get('category', '')
    if category_filter:
        items = items.filter(category=category_filter)
    
    # Get all categories for filter dropdown
    categories = Item.CATEGORY_CHOICES
    
    context = {
        'items': items,
        'categories': categories,
    }
    
    return render(request, 'lfapp/found_items.html', context)

@login_required
def admin_dashboard_view(request):
    """Admin dashboard with statistics"""
    # Check if user is admin
    if not request.user.is_admin_user():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')
    
    # Get all items
    all_items = Item.objects.select_related('posted_by').order_by('-created_at')
    
    # Calculate statistics
    total_items = all_items.count()
    lost_count = all_items.filter(item_type='lost').count()
    found_count = all_items.filter(item_type='found').count()
    
    # Calculate percentages
    lost_percentage = round((lost_count / total_items * 100), 0) if total_items > 0 else 0
    found_percentage = round((found_count / total_items * 100), 0) if total_items > 0 else 0
    
    # Get unique category count
    category_count = all_items.values('category').distinct().count()
    
    # Get pending items count for moderation queue badge
    pending_count = all_items.filter(status='pending').count()
    
    context = {
        'all_items': all_items,
        'total_items': total_items,
        'lost_count': lost_count,
        'found_count': found_count,
        'lost_percentage': int(lost_percentage),
        'found_percentage': int(found_percentage),
        'category_count': category_count,
        'pending_count': pending_count,
    }
    
    return render(request, 'lfapp/admin_dashboard.html', context)

@login_required
def admin_moderation_queue_view(request):
    """Admin moderation queue - Visual preview and quick approve/reject"""
    from django.utils import timezone
    
    # Check if user is admin
    if not request.user.is_admin_user():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')
    
    # Get pending items for moderation
    pending_items = Item.objects.filter(
        status='pending'
    ).select_related('posted_by').order_by('-created_at')
    
    # Get all items for statistics
    all_items = Item.objects.all()
    pending_count = pending_items.count()
    approved_count = all_items.filter(status='approved').count()
    rejected_count = all_items.filter(status='rejected').count()
    claimed_count = all_items.filter(status='claimed').count()
    
    context = {
        'pending_items': pending_items,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'claimed_count': claimed_count,
    }
    
    return render(request, 'lfapp/admin_moderation.html', context)

@login_required
def admin_quick_approve_view(request, item_id):
    """Admin: Quick approve from moderation queue"""
    from django.shortcuts import get_object_or_404
    from django.utils import timezone
    
    if not request.user.is_admin_user():
        messages.error(request, 'You do not have permission to perform this action.')
        return redirect('home')
    
    item = get_object_or_404(Item, id=item_id)
    
    if request.method == 'POST':
        item.status = 'approved'
        item.approved_by = request.user
        item.approved_at = timezone.now()
        item.save()
        
        # Send approval email to item poster
        send_item_approved_email(item, request)
        
        messages.success(request, f'✅ Approved: "{item.title}" is now visible to everyone!')
        return redirect('admin_moderation')
    
    return redirect('admin_moderation')

@login_required
def admin_quick_reject_view(request, item_id):
    """Admin: Quick reject from moderation queue"""
    from django.shortcuts import get_object_or_404
    
    if not request.user.is_admin_user():
        messages.error(request, 'You do not have permission to perform this action.')
        return redirect('home')
    
    item = get_object_or_404(Item, id=item_id)
    
    if request.method == 'POST':
        item.status = 'rejected'
        item.save()
        
        # Send rejection email to item poster
        send_item_rejected_email(item, request)
        
        messages.warning(request, f'❌ Rejected: "{item.title}" will not be published.')
        return redirect('admin_moderation')
    
    return redirect('admin_moderation')

def logout_view(request):
    """Logout user"""
    logout(request)
    return redirect('landing')

@login_required
def post_lost_item_view(request):
    """Form to post a lost item"""
    # Check if user can post items
    if not request.user.can_post_items():
        messages.error(request, 'You must be a verified user to post items.')
        return redirect('home')
    
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES, item_type='lost')
        if form.is_valid():
            item = form.save(commit=False)
            item.item_type = 'lost'
            item.posted_by = request.user
            item.status = 'pending'  # Items need admin approval
            item.save()
            
            # Send pending approval email
            send_item_pending_email(item, request)
            
            messages.success(request, 'Your lost item has been submitted and is pending approval.')
            return redirect('lost_items')
    else:
        form = ItemForm(item_type='lost')
    
    context = {
        'form': form,
        'item_type': 'lost',
    }
    return render(request, 'lfapp/post_item.html', context)

@login_required
def post_found_item_view(request):
    """Form to post a found item"""
    # Check if user can post items
    if not request.user.can_post_items():
        messages.error(request, 'You must be a verified user to post items.')
        return redirect('home')
    
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES, item_type='found')
        if form.is_valid():
            item = form.save(commit=False)
            item.item_type = 'found'
            item.posted_by = request.user
            item.status = 'pending'  # Items need admin approval
            item.save()
            
            # Send pending approval email
            send_item_pending_email(item, request)
            
            messages.success(request, 'Your found item has been submitted and is pending approval.')
            return redirect('found_items')
    else:
        form = ItemForm(item_type='found')
    
    context = {
        'form': form,
        'item_type': 'found',
    }
    return render(request, 'lfapp/post_item.html', context)

def claimed_items_view(request):
    """View all completed items (both claimed and found) - Public access allowed"""
    items = Item.objects.filter(
        status__in=['claimed', 'found']
    ).select_related('posted_by', 'claimed_by').order_by('-completed_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        items = items.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(claimed_by__email__icontains=search_query)
        )
    
    # Category filter
    category_filter = request.GET.get('category', '')
    if category_filter:
        items = items.filter(category=category_filter)
    
    # Get all categories for filter dropdown
    categories = Item.CATEGORY_CHOICES
    
    context = {
        'items': items,
        'categories': categories,
    }
    
    return render(request, 'lfapp/claimed_items.html', context)

@login_required
def edit_item_view(request, item_id):
    """Edit an existing item - Only owner can edit"""
    from django.shortcuts import get_object_or_404
    
    item = get_object_or_404(Item, id=item_id)
    
    # Check if user is the owner
    if item.posted_by != request.user:
        messages.error(request, 'You can only edit your own items.')
        return redirect('home')
    
    # Check if user can still post items
    if not request.user.can_post_items():
        messages.error(request, 'You must be a verified user to edit items.')
        return redirect('home')
    
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES, instance=item, item_type=item.item_type)
        if form.is_valid():
            updated_item = form.save(commit=False)
            # Keep original posted_by and reset to pending if not admin
            updated_item.posted_by = item.posted_by
            status_changed_to_pending = False
            if not request.user.is_admin_user():
                if updated_item.status != 'pending':
                    status_changed_to_pending = True
                updated_item.status = 'pending'  # Needs re-approval after edit
            updated_item.save()
            
            # Send pending email if status changed to pending
            if status_changed_to_pending:
                send_item_pending_email(updated_item, request)
            
            messages.success(request, 'Your item has been updated and is pending approval.')
            return redirect('lost_items' if item.item_type == 'lost' else 'found_items')
    else:
        form = ItemForm(instance=item, item_type=item.item_type)
    
    context = {
        'form': form,
        'item_type': item.item_type,
        'item': item,
        'is_edit': True,
    }
    return render(request, 'lfapp/post_item.html', context)

@login_required
def toggle_item_listing_view(request, item_id):
    """Toggle item active status (delist/relist) - Only owner can toggle"""
    from django.shortcuts import get_object_or_404
    
    item = get_object_or_404(Item, id=item_id)
    
    # Check if user is the owner
    if item.posted_by != request.user:
        messages.error(request, 'You can only manage your own items.')
        return redirect('home')
    
    # Prevent delisting claimed items - they are success stories!
    if not item.can_be_delisted():
        messages.error(request, '❌ Cannot delist claimed items. These remain as success stories showing the app works!')
        return redirect('lost_items' if item.item_type == 'lost' else 'found_items')
    
    # Toggle is_active status
    item.is_active = not item.is_active
    item.save()
    
    if item.is_active:
        messages.success(request, f'Your item "{item.title}" is now listed publicly.')
    else:
        messages.success(request, f'Your item "{item.title}" has been delisted and is now hidden from public view.')
    
    return redirect('lost_items' if item.item_type == 'lost' else 'found_items')

@login_required
def delete_item_view(request, item_id):
    """Delete an item permanently - Only owner can delete, claimed items protected"""
    from django.shortcuts import get_object_or_404
    import os
    
    item = get_object_or_404(Item, id=item_id)
    
    # Check if user is the owner
    if item.posted_by != request.user:
        messages.error(request, 'You can only delete your own items.')
        return redirect('home')
    
    # Prevent deletion of claimed items - they are success stories!
    if not item.can_be_deleted():
        messages.error(request, '❌ Cannot delete claimed items. These must remain as success stories and proof that the app works! Contact admin if you have privacy concerns.')
        return redirect('lost_items' if item.item_type == 'lost' else 'found_items')
    
    if request.method == 'POST':
        # Delete the image file if it exists
        if item.image:
            try:
                if os.path.isfile(item.image.path):
                    os.remove(item.image.path)
            except Exception as e:
                print(f"Error deleting image: {e}")
        
        item_title = item.title
        item_type = item.item_type
        item.delete()
        
        messages.success(request, f'🗑️ "{item_title}" has been permanently deleted.')
        return redirect('lost_items' if item_type == 'lost' else 'found_items')
    
    # Show confirmation page
    context = {
        'item': item,
    }
    return render(request, 'lfapp/confirm_delete.html', context)

@login_required
def send_message_view(request, item_id):
    """Send a message to item poster - Only verified PSU users"""
    from django.shortcuts import get_object_or_404
    from .models import ContactMessage
    
    item = get_object_or_404(Item, id=item_id)
    
    # Check if user is PSU verified
    if not request.user.is_psu_user():
        messages.error(request, 'Only verified PSU users can contact item posters.')
        return redirect('home')
    
    # Can't message your own post
    if item.posted_by == request.user:
        messages.error(request, 'You cannot message your own post.')
        return redirect('home')
    
    if request.method == 'POST':
        subject = request.POST.get('subject', '').strip()
        message_text = request.POST.get('message', '').strip()
        sender_phone = request.POST.get('phone', '').strip()
        
        if not subject or not message_text:
            messages.error(request, 'Subject and message are required.')
            return render(request, 'lfapp/send_message.html', {'item': item})
        
        # Create message
        contact_message = ContactMessage.objects.create(
            item=item,
            sender=request.user,
            recipient=item.posted_by,
            subject=subject,
            message=message_text,
            sender_phone=sender_phone
        )
        
        # Send email notification via SendGrid
        from django.core.mail import send_mail
        from django.conf import settings
        
        email_subject = f'[HanApp] New message about your {item.item_type} item: {item.title}'
        email_body = f"""
Hello {item.posted_by.get_full_name() or item.posted_by.email},

You have received a new message about your {item.item_type} item "{item.title}".

From: {request.user.get_full_name() or request.user.email}
Email: {request.user.email}
{f'Phone: {sender_phone}' if sender_phone else ''}

Subject: {subject}

Message:
{message_text}

---
View all your messages at: {request.build_absolute_uri('/messages/inbox/')}
Reply to: {request.user.email}

This is an automated message from HanApp - PSU Lost and Found
"""
        
        try:
            send_mail(
                subject=email_subject,
                message=email_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[item.posted_by.email],
                fail_silently=False,
            )
        except Exception as e:
            # Log error but don't fail the message creation
            print(f"Email sending failed: {e}")
        
        messages.success(request, f'Your message has been sent to {item.posted_by.get_full_name() or item.posted_by.email}!')
        return redirect('lost_items' if item.item_type == 'lost' else 'found_items')
    
    return render(request, 'lfapp/send_message.html', {'item': item})

@login_required
def messages_inbox_view(request):
    """View all received messages"""
    from .models import ContactMessage
    
    # Get only root messages (not replies) received by user
    received_messages = ContactMessage.objects.filter(
        recipient=request.user,
        parent_message__isnull=True
    ).select_related('sender', 'item').order_by('-created_at')
    
    # Mark messages as read when viewing inbox
    received_messages.filter(is_read=False).update(is_read=True)
    
    context = {
        'messages': received_messages,
    }
    return render(request, 'lfapp/messages_inbox.html', context)

@login_required
def messages_sent_view(request):
    """View all sent messages"""
    from .models import ContactMessage
    
    # Get only root messages (not replies) sent by user
    sent_messages = ContactMessage.objects.filter(
        sender=request.user,
        parent_message__isnull=True
    ).select_related('recipient', 'item').order_by('-created_at')
    
    context = {
        'messages': sent_messages,
    }
    return render(request, 'lfapp/messages_sent.html', context)

@login_required
def message_thread_view(request, message_id):
    """View a message conversation thread and reply"""
    from django.shortcuts import get_object_or_404
    from .models import ContactMessage
    
    # Get the root message
    root_message = get_object_or_404(ContactMessage, id=message_id)
    
    # Check if user is part of this conversation
    if root_message.sender != request.user and root_message.recipient != request.user:
        messages.error(request, 'You do not have permission to view this conversation.')
        return redirect('messages_inbox')
    
    # Get all messages in thread
    thread_messages = root_message.get_thread_messages()
    
    # Mark unread messages as read for current user
    thread_messages.filter(recipient=request.user, is_read=False).update(is_read=True)
    
    # Handle reply submission
    if request.method == 'POST':
        message_text = request.POST.get('message', '').strip()
        image = request.FILES.get('image')
        
        if not message_text and not image:
            messages.error(request, 'Please provide a message or image.')
            return redirect('message_thread', message_id=message_id)
        
        # Determine recipient (the other person in conversation)
        recipient = root_message.sender if root_message.recipient == request.user else root_message.recipient
        
        # Create reply message
        reply = ContactMessage.objects.create(
            item=root_message.item,
            sender=request.user,
            recipient=recipient,
            subject=f"Re: {root_message.subject}",
            message=message_text,
            image=image,
            parent_message=root_message if root_message.parent_message is None else root_message.parent_message
        )
        
        # Send email notification via SendGrid
        from django.core.mail import EmailMessage
        from django.conf import settings
        
        email_subject = f'[HanApp] New reply about: {root_message.item.title}'
        email_body = f"""
Hello {recipient.get_full_name() or recipient.email},

You have received a new reply from {request.user.get_full_name() or request.user.email} about the {root_message.item.item_type} item "{root_message.item.title}".

Message:
{message_text}

---
View the full conversation at: {request.build_absolute_uri(f'/messages/thread/{root_message.id}/')}

This is an automated message from HanApp - PSU Lost and Found
"""
        
        try:
            email = EmailMessage(
                subject=email_subject,
                body=email_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient.email],
            )
            
            # Attach image if provided
            if image:
                email.attach(image.name, image.read(), image.content_type)
            
            email.send(fail_silently=False)
        except Exception as e:
            print(f"Email sending failed: {e}")
        
        messages.success(request, 'Your reply has been sent!')
        return redirect('message_thread', message_id=message_id)
    
    context = {
        'root_message': root_message,
        'thread_messages': thread_messages,
        'other_user': root_message.sender if root_message.recipient == request.user else root_message.recipient,
    }
    return render(request, 'lfapp/message_thread.html', context)

@login_required
def mark_item_complete_view(request, item_id):
    """Mark an item as found (for lost items) or claimed (for found items)"""
    from django.shortcuts import get_object_or_404
    from django.utils import timezone
    from .forms import ItemCompletionForm
    
    item = get_object_or_404(Item, id=item_id)
    
    # Check if user is the owner
    if item.posted_by != request.user:
        messages.error(request, 'You can only mark your own items as complete.')
        return redirect('home')
    
    # Check if item is approved
    if item.status != 'approved':
        messages.error(request, 'Only approved items can be marked as complete.')
        return redirect('home')
    
    # Determine the completion type based on item_type
    completion_type = 'found' if item.item_type == 'lost' else 'claimed'
    action_label = 'Mark as Found' if item.item_type == 'lost' else 'Mark as Claimed'
    person_label = 'Returner' if item.item_type == 'lost' else 'Claimer'
    
    if request.method == 'POST':
        form = ItemCompletionForm(request.POST)
        if form.is_valid():
            # Update item with completion details
            item.completion_name = form.cleaned_data['completion_name']
            item.completion_email = form.cleaned_data['completion_email']
            item.completed_at = timezone.now()
            
            # Set status based on item type
            if item.item_type == 'lost':
                item.status = 'found'
            else:  # found item
                item.status = 'claimed'
            
            item.save()
            
            success_message = f'✅ Your {item.item_type} item "{item.title}" has been marked as {completion_type}!'
            messages.success(request, success_message)
            
            # Redirect to appropriate items list
            return redirect('claimed_items')
    else:
        form = ItemCompletionForm()
    
    context = {
        'form': form,
        'item': item,
        'action_label': action_label,
        'person_label': person_label,
        'completion_type': completion_type,
    }
    return render(request, 'lfapp/mark_complete.html', context)

