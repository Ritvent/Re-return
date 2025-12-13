from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
import json
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Subquery, OuterRef, Exists, Case, When, Value, CharField, Max
from django.core.paginator import Paginator
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.utils import timezone
from itertools import chain
from operator import attrgetter
import os

from .models import Item, CustomUser, ContactMessage
from .forms import ItemForm, ItemCompletionForm
from .utils import validate_image_file
from django.core.exceptions import ValidationError
from .email_notifications import send_item_pending_email, send_item_approved_email, send_item_rejected_email, send_role_change_email, send_admin_new_item_notification

def annotate_user_conversations(queryset, user):
    """Annotate items with existing thread ID for the current user"""
    if not user.is_authenticated:
        return queryset
    
    # Find the root message ID sent by this user for this item
    thread_subquery = ContactMessage.objects.filter(
        item=OuterRef('pk'),
        sender=user,
        parent_message__isnull=True
    ).values('pk')[:1]
    
    return queryset.annotate(
        existing_thread_id=Subquery(thread_subquery)
    )

def landing_view(request):
    """Landing page with login form"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
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
        is_active=True,
        is_archived=False
    ).select_related('posted_by').order_by('-created_at')
    recent_lost = annotate_user_conversations(recent_lost, request.user)[:4]
    
    # Get recent found items (limit to 4)
    recent_found = Item.objects.filter(
        item_type='found',
        status='approved',
        is_active=True,
        is_archived=False
    ).select_related('posted_by').order_by('-created_at')
    recent_found = annotate_user_conversations(recent_found, request.user)[:4]
    
    # Get recent activities: recent posts + recent completions
    # Recent posts (both lost and found, approved and active)
    recent_posts = Item.objects.filter(
        status='approved',
        is_active=True,
        is_archived=False
    ).select_related('posted_by').order_by('-created_at')
    recent_posts = annotate_user_conversations(recent_posts, request.user)[:10]
    
    # Recent completed items (claimed and found)
    recent_completed = Item.objects.filter(
        status__in=['claimed', 'found'],
        is_active=True,
        is_archived=False
    ).select_related('posted_by', 'claimed_by').order_by('-completed_at')
    recent_completed = annotate_user_conversations(recent_completed, request.user)[:10]
    
    # Combine and sort by most recent activity (either created_at or completed_at)
    all_activities = list(chain(recent_posts, recent_completed))
    # Remove duplicates (items that are both posted and completed)
    seen_ids = set()
    unique_activities = []
    for item in all_activities:
        if item.id not in seen_ids:
            seen_ids.add(item.id)
            unique_activities.append(item)
    
    # Sort by most recent activity (completed_at for completed items, created_at for posts)
    def get_activity_time(item):
        if item.status in ['claimed', 'found'] and item.completed_at:
            return item.completed_at
        return item.created_at
    
    recent_activities = sorted(unique_activities, key=get_activity_time, reverse=True)[:10]
    
    context = {
        'recent_lost': recent_lost,
        'recent_found': recent_found,
        'recent_activities': recent_activities,
    }
    
    return render(request, 'lfapp/home.html', context)


def lost_items_view(request):
    """View all lost items with search and filter - Public access allowed"""
    # Show approved items to everyone, plus pending items to their owners
    if request.user.is_authenticated:
        items = Item.objects.filter(
            item_type='lost',
            is_archived=False
        ).filter(
            Q(status='approved', is_active=True) | Q(posted_by=request.user)
        ).exclude(status='found').select_related('posted_by').order_by('-created_at')
    else:
        items = Item.objects.filter(
            item_type='lost',
            status__in=['approved'],
            is_archived=False
        ).select_related('posted_by').order_by('-created_at')
    
    items = annotate_user_conversations(items, request.user)

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
            item_type='found',
            is_archived=False
        ).filter(
            Q(status='approved', is_active=True) | Q(posted_by=request.user)
        ).exclude(status='claimed').select_related('posted_by').order_by('-created_at')
    else:
        items = Item.objects.filter(
            item_type='found',
            status__in=['approved'],
            is_archived=False
        ).select_related('posted_by').order_by('-created_at')
    
    items = annotate_user_conversations(items, request.user)

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
    
    # Get all items base queryset (exclude archived)
    all_items = Item.objects.filter(is_archived=False).select_related('posted_by').order_by('-created_at')
    
    # Get filter parameters
    item_type_filter = request.GET.get('type', '')
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    date_preset = request.GET.get('date_preset', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Handle date preset options
    from datetime import timedelta
    today = timezone.now().date()
    
    if date_preset == 'today':
        date_from = str(today)
        date_to = str(today)
    elif date_preset == 'last-7-days':
        date_from = str(today - timedelta(days=7))
        date_to = str(today)
    elif date_preset == 'last-30-days':
        date_from = str(today - timedelta(days=30))
        date_to = str(today)
    elif date_preset == 'custom':
        # Use the custom date_from and date_to values from the form
        pass
    else:
        # All time - clear date filters
        date_from = ''
        date_to = ''
    
    # Apply filters
    filtered_items = all_items
    if item_type_filter:
        filtered_items = filtered_items.filter(item_type=item_type_filter)
    if status_filter:
        filtered_items = filtered_items.filter(status=status_filter)
    if search_query:
        filtered_items = filtered_items.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(posted_by__email__icontains=search_query) |
            Q(posted_by__first_name__icontains=search_query) |
            Q(posted_by__last_name__icontains=search_query)
        )
    if date_from:
        filtered_items = filtered_items.filter(created_at__date__gte=date_from)
    if date_to:
        filtered_items = filtered_items.filter(created_at__date__lte=date_to)
    
    # Calculate statistics (from all items, not filtered)
    total_items = all_items.count()
    lost_count = all_items.filter(item_type='lost').count()
    found_count = all_items.filter(item_type='found').count()
    
    # Calculate percentages
    lost_percentage = round((lost_count / total_items * 100), 0) if total_items > 0 else 0
    found_percentage = round((found_count / total_items * 100), 0) if total_items > 0 else 0
    
    # Get unique user count
    user_count = CustomUser.objects.filter(is_superuser=False).count()
    
    # Get pending items count for moderation queue badge
    pending_count = all_items.filter(status='pending').count()
    
    # Pagination
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    paginator = Paginator(filtered_items, 10)  # 10 items per page
    page = request.GET.get('page')
    
    try:
        items_page = paginator.page(page)
    except PageNotAnInteger:
        items_page = paginator.page(1)
    except EmptyPage:
        items_page = paginator.page(paginator.num_pages)
    
    context = {
        'all_items': items_page,
        'total_items': total_items,
        'lost_count': lost_count,
        'found_count': found_count,
        'lost_percentage': int(lost_percentage),
        'found_percentage': int(found_percentage),
        'user_count': user_count,
        'pending_count': pending_count,
        'item_type_filter': item_type_filter,
        'status_filter': status_filter,
        'search_query': search_query,
        'date_preset': date_preset,
        'date_from': date_from if date_preset == 'custom' else '',
        'date_to': date_to if date_preset == 'custom' else '',
        'filtered_count': filtered_items.count(),
    }
    
    return render(request, 'lfapp/admin_dashboard.html', context)

@login_required
def admin_moderation_queue_view(request):
    """Admin moderation queue - Visual preview and quick approve/reject"""
    # Check if user is admin
    if not request.user.is_admin_user():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')
    
    # Get pending items for moderation (exclude archived)
    pending_items = Item.objects.filter(
        status='pending',
        is_archived=False
    ).select_related('posted_by').order_by('-created_at')
    
    # Get all items for statistics (exclude archived)
    all_items = Item.objects.filter(is_archived=False)
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

@login_required
def admin_user_management_view(request):
    """Admin: Manage users and roles"""
    if not request.user.is_admin_user():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')
    
    # Get all users
    users = CustomUser.objects.all().order_by('-date_joined')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    # Role filter
    role_filter = request.GET.get('role', '')
    if role_filter:
        users = users.filter(role=role_filter)
    
    context = {
        'users': users,
        'role_choices': CustomUser.ROLE_CHOICES,
    }
    
    return render(request, 'lfapp/admin_users.html', context)

@login_required
def admin_promote_user_view(request, user_id):
    """Admin: Promote/Demote user role"""
    if not request.user.is_admin_user():
        messages.error(request, 'You do not have permission to perform this action.')
        return redirect('home')
    
    user_to_edit = get_object_or_404(CustomUser, id=user_id)
    
    # Prevent modifying own role
    # Prevent modifying own role
    # Logic handled inside POST for step down, but for GET we can just show the page (or redirect if needed)
    
    if request.method == 'POST':
        new_role = request.POST.get('role')
        is_self_action = request.user == user_to_edit
        
        # 1. Self-Action (Step Down)
        if is_self_action:
            if new_role == 'verified' and request.user.role == 'admin':
                # Allow admin to step down
                user_to_edit.role = 'verified'
                user_to_edit.save()
                
                # Send email for step down
                send_role_change_email(user_to_edit, 'verified', actor=request.user)
                
                messages.success(request, 'You have successfully stepped down from Admin role. Thank you for your service !')
                return redirect('home') # Redirect to home as they lost access
            else:
                messages.error(request, 'Invalid action on yourself.')
                return redirect('admin_users')

        # 2. Superadmin Actions (Can do anything)
        if request.user.is_superuser:
            if new_role in dict(CustomUser.ROLE_CHOICES):
                user_to_edit.role = new_role
                if new_role in ['verified', 'admin']:
                    user_to_edit.is_verified = True
                user_to_edit.save()
                
                # Send email notification
                send_role_change_email(user_to_edit, new_role, actor=request.user)
                
                messages.success(request, f'User {user_to_edit.email} role updated to {user_to_edit.get_role_display()}.')
            return redirect('admin_users')

        # 3. Admin Actions (Restricted)
        if request.user.role == 'admin':
            # Cannot modify Superusers
            if user_to_edit.is_superuser:
                messages.error(request, 'You cannot modify a Super Administrator.')
                return redirect('admin_users')
            
            # Cannot demote others (only promote)
            # Logic: If current role is 'admin', cannot change to 'verified' or 'public'
            if user_to_edit.role == 'admin' and new_role != 'admin':
                 messages.error(request, 'Admins cannot demote other Admins.')
                 return redirect('admin_users')

            # Prevent demoting corporate users to public (existing rule)
            if new_role == 'public' and user_to_edit.has_psu_email:
                messages.error(request, 'Corporate users (PSU email) cannot be demoted to Public User.')
                return redirect('admin_users')
            
            # Allow promotion
            if new_role in dict(CustomUser.ROLE_CHOICES):
                user_to_edit.role = new_role
                if new_role in ['verified', 'admin']:
                    user_to_edit.is_verified = True
                user_to_edit.save()
                
                # Send email notification
                send_role_change_email(user_to_edit, new_role, actor=request.user)
                
                messages.success(request, f'User {user_to_edit.email} role updated to {user_to_edit.get_role_display()}.')
            return redirect('admin_users')
            
        messages.error(request, 'You do not have permission to perform this action.')
        return redirect('admin_users')
            
    return redirect('admin_users')

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
            
            # Auto-approve for admins, otherwise pending
            if request.user.is_admin_user():
                item.status = 'approved'
                item.save()
                messages.success(request, 'Your lost item has been posted successfully.')
            else:
                item.status = 'pending'
                item.save()
                # Send emails for pending items
                send_item_pending_email(item, request)
                send_admin_new_item_notification(item)
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
            
            # Auto-approve for admins, otherwise pending
            if request.user.is_admin_user():
                item.status = 'approved'
                item.save()
                messages.success(request, 'Your found item has been posted successfully.')
            else:
                item.status = 'pending'
                item.save()
                # Send emails for pending items
                send_item_pending_email(item, request)
                send_admin_new_item_notification(item)
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
        status__in=['claimed', 'found'],
        is_archived=False
    ).select_related('posted_by', 'claimed_by').order_by('-completed_at')
    
    items = annotate_user_conversations(items, request.user)

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
        
        messages.success(request, f'"{item_title}" has been permanently deleted.')
        return redirect('lost_items' if item_type == 'lost' else 'found_items')
    
    # Show confirmation page
    context = {
        'item': item,
    }
    return render(request, 'lfapp/confirm_delete.html', context)

@login_required
def send_message_view(request, item_id):
    """Send a message to item poster - Only verified PSU users"""
    item = get_object_or_404(Item, id=item_id)
    
    # Check if user is PSU verified
    if not request.user.is_psu_user():
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'Only verified PSU users can contact item posters.'}, status=403)
        messages.error(request, 'Only verified PSU users can contact item posters.')
        return redirect('home')
    
    # Can't message your own post
    if item.posted_by == request.user:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'You cannot message your own post.'}, status=400)
        messages.error(request, 'You cannot message your own post.')
        return redirect('home')
    
    if request.method == 'POST':
        subject = request.POST.get('subject', '').strip()
        message_text = request.POST.get('message', '').strip()
        sender_phone = request.POST.get('phone', '').strip()
        
        if not subject or not message_text:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': 'Please fill in all fields.'}, status=400)
            messages.error(request, 'Please fill in all fields.')
            return redirect('send_message', item_id=item_id)
            
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
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'message': 'Message sent successfully!'})

        messages.success(request, f'Your message has been sent to {item.posted_by.get_full_name() or item.posted_by.email}!')
        return redirect('lost_items' if item.item_type == 'lost' else 'found_items')
    

    return redirect('home')

@login_required
def messages_inbox_view(request):
    """View all conversations (unified inbox + sent)"""
    
    # Get all root messages where user is either sender or recipient
    # Exclude threads deleted by the current user
    all_messages = ContactMessage.objects.filter(
        Q(sender=request.user) | Q(recipient=request.user),
        parent_message__isnull=True
    ).exclude(
        Q(sender=request.user, deleted_by_sender=True) |
        Q(recipient=request.user, deleted_by_recipient=True)
    ).select_related('sender', 'recipient', 'item')
    
    # Annotate with the latest message timestamp in the thread
    latest_message_time = ContactMessage.objects.filter(
        Q(id=OuterRef('pk')) | Q(parent_message_id=OuterRef('pk'))
    ).values('created_at').order_by('-created_at')[:1]
    
    all_messages = all_messages.annotate(
        latest_msg_time=Subquery(latest_message_time)
    )
    
    # Order by latest message time (most recent conversations first)
    all_messages = all_messages.order_by('-latest_msg_time')
    
    # Annotate with conversation partner and direction
    all_messages = all_messages.annotate(
        # The "other user" in the conversation
        other_user_id=Case(
            When(sender=request.user, then='recipient__id'),
            default='sender__id'
        ),
        # Direction: True if user received this message
        is_incoming=Case(
            When(recipient=request.user, then=Value(True)),
            default=Value(False),
            output_field=CharField()
        )
    )
    
    # Annotate with unread status (check if ANY message in thread is unread for current user)
    unread_in_thread = ContactMessage.objects.filter(
        Q(id=OuterRef('pk')) | Q(parent_message_id=OuterRef('pk')),
        recipient=request.user,
        is_read=False
    )
    all_messages = all_messages.annotate(
        has_unread=Exists(unread_in_thread)
    )
    
    # Annotate with the latest message text, is_read status, and sender in the thread
    latest_message_qs = ContactMessage.objects.filter(
        Q(id=OuterRef('pk')) | Q(parent_message_id=OuterRef('pk'))
    ).order_by('-created_at')
    
    all_messages = all_messages.annotate(
        latest_message_text=Subquery(latest_message_qs.values('message')[:1]),
        latest_message_image=Subquery(latest_message_qs.values('image')[:1]),
        latest_msg_is_read=Subquery(latest_message_qs.values('is_read')[:1]),
        latest_msg_sender_id=Subquery(latest_message_qs.values('sender_id')[:1])
    )
    
    context = {
        'messages': all_messages,
    }
    return render(request, 'lfapp/messages_inbox.html', context)


@login_required
def messages_sent_view(request):
    """Redirect to unified messages view"""
    from django.shortcuts import redirect
    return redirect('messages_inbox')

@login_required
def delete_thread_view(request, message_id):
    """Soft delete a message thread for the current user only"""
    # Get the root message
    root_message = get_object_or_404(
        ContactMessage,
        id=message_id,
        parent_message__isnull=True
    )
    
    # Verify user is part of this conversation
    if request.user != root_message.sender and request.user != root_message.recipient:
        messages.error(request, 'You do not have permission to delete this conversation.')
        return redirect('messages_inbox')
    
    # Set the appropriate deletion flag
    if request.user == root_message.sender:
        root_message.deleted_by_sender = True
    else:
        root_message.deleted_by_recipient = True
    
    root_message.save()
    return redirect('messages_inbox')

@login_required
def message_thread_view(request, message_id):
    """View a message conversation thread and reply"""
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
        # Check if it's an AJAX request (meaning it came from JavaScript, not a normal form submit)
        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
        
        # If JSON content type, parse body. Otherwise (FormData/Multipart), use request.POST
        # We need to check this because sometimes we send JSON and sometimes we send Form Data
        if request.content_type == 'application/json':
            try:
                # Try to read the JSON data from the request body
                data = json.loads(request.body)
                message_text = data.get('message', '').strip()
            except json.JSONDecodeError:
                # If it fails, just set message to empty
                message_text = ''
        else:
            # If it's not JSON, just get it from the normal POST dictionary
            message_text = request.POST.get('message', '').strip()
            
        image = request.FILES.get('image')
        
        if not message_text and not image:
            if is_ajax:
                return JsonResponse({'status': 'error', 'message': 'Please provide a message or image.'}, status=400)
            messages.error(request, 'Please provide a message or image.')
            return redirect('message_thread', message_id=message_id)
        
        # Validate image extension and content
        if image:
            try:
                validate_image_file(image)
            except ValidationError as e:
                if is_ajax:
                    return JsonResponse({'status': 'error', 'message': e.message}, status=400)
                messages.error(request, e.message)
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
            
        if is_ajax:
            # If it was an AJAX request, return a JSON response so the page doesn't reload
            return JsonResponse({
                'status': 'success',
                'message': 'Reply sent successfully!',
                'data': {
                    'id': reply.id,
                    'message': reply.message,
                    'created_at': reply.created_at.strftime("%b %d, %I:%M %p"), # Format: M d, g:i A
                    'sender_id': request.user.id,
                    'is_me': True, # This tells the frontend that I sent this message
                    'sender_name': request.user.get_full_name() or request.user.username,
                    'sender_initial': (request.user.get_full_name() or request.user.username)[0].upper(),
                    'profile_pic': request.user.google_profile_picture if request.user.google_profile_picture else None,
                    'image_url': reply.image.url if reply.image else None
                }
            })

        messages.success(request, 'Reply sent successfully!')
        return redirect('message_thread', message_id=message_id)
    
    context = {
        'root_message': root_message,
        'thread_messages': thread_messages,
        'other_user': root_message.sender if root_message.recipient == request.user else root_message.recipient,
    }
    return render(request, 'lfapp/message_thread.html', context)

@login_required
def get_thread_messages_view(request, thread_id):
    """API to get new messages for a thread (Smart Polling)"""
    # Get the main message thread
    root_message = get_object_or_404(ContactMessage, id=thread_id)
    
    # Check permission - make sure the user is allowed to see this
    if root_message.sender != request.user and root_message.recipient != request.user:
        return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
    
    # Get last message ID from queue param to fetch only new messages
    # important so we don't download the whole chat history every time
    last_id = request.GET.get('last_id')
    
    messages_qs = root_message.get_thread_messages()
    
    # If we have a last_id, only get messages that came AFTER that one
    if last_id:
        messages_qs = messages_qs.filter(id__gt=last_id)
        
    
    messages_qs.filter(recipient=request.user, is_read=False).update(is_read=True)
    
    # Prepare the data list to send back to the frontend
    data = []
    for msg in messages_qs:
        data.append({
            'id': msg.id,
            'message': msg.message,
            'created_at': msg.created_at.strftime("%b %d, %I:%M %p"), # Short, Ex: Dec, 01, not military time, min, period
            'sender_id': msg.sender.id,
            'is_me': msg.sender == request.user, # Check if current user sent this message
            'sender_name': msg.sender.get_full_name() or msg.sender.username,
            'sender_initial': (msg.sender.get_full_name() or msg.sender.username)[0].upper(),
            'profile_pic': msg.sender.google_profile_picture if msg.sender.google_profile_picture else None,
            'image_url': msg.image.url if msg.image else None
        })
        
    return JsonResponse({'status': 'success', 'messages': data})

@login_required
def delete_message_view(request, message_id):
    """Delete a message"""
    message = get_object_or_404(ContactMessage, id=message_id)
    
    # Check permission
    if message.sender != request.user:
        messages.error(request, 'You can only delete your own messages.')
        return redirect('messages_inbox')
    
    # Determine redirect URL
    if message.parent_message:
        # It's a reply, go back to thread
        redirect_url = f'/messages/thread/{message.parent_message.id}/'
    else:
        # It's a root message, go back to inbox (thread is gone)
        redirect_url = 'messages_inbox'
        
    # Soft delete
    message.is_deleted = True
    message.save()
    
    # Delete image file if exists (optional: keep it if you want to restore, but usually good to save space)
    # For soft delete, we might want to keep the image record but maybe delete the file?
    # Let's keep the file for now in case of restoration, or delete it if privacy is key.
    # User said "message removed by user", implying content is gone.
    if message.image:
        try:
            if os.path.isfile(message.image.path):
                os.remove(message.image.path)
            message.image = None # Remove reference
            message.save()
        except Exception as e:
            print(f"Error deleting message image: {e}")
            
    messages.success(request, 'Message removed.')
    
    if redirect_url == 'messages_inbox':
        return redirect('messages_inbox')
    else:
        return redirect(redirect_url)

@login_required
def mark_item_complete_view(request, item_id):
    """Mark an item as found (for lost items) or claimed (for found items)"""
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


@login_required
def admin_archive_item_view(request, item_id):
    """Admin archive/delete an item with reason and optional notes"""
    # Check if user is admin
    if not request.user.is_admin_user():
        messages.error(request, 'You do not have permission to perform this action.')
        return redirect('home')
    
    item = get_object_or_404(Item, id=item_id)
    
    if request.method == 'POST':
        archive_reason = request.POST.get('reason', 'other')
        archive_notes = request.POST.get('notes', '')
        
        # Archive the item
        item.is_archived = True
        item.archived_by = request.user
        item.archived_at = timezone.now()
        item.archive_reason = archive_reason
        item.archive_notes = archive_notes
        item.save()
        
        # Send email notification to the poster
        from .email_notifications import send_item_archived_email
        send_item_archived_email(item, request.user, archive_reason, archive_notes)
        
        messages.success(request, f'Item "{item.title}" has been archived.')
        
        # Handle AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Item archived successfully'})
        
        # Redirect back to where we came from
        next_url = request.POST.get('next', 'admin_dashboard')
        return redirect(next_url)
    
    # GET request - shouldn't happen normally, redirect to dashboard
    return redirect('admin_dashboard')


@login_required
def admin_permanent_delete_view(request, item_id):
    """Permanently delete an archived item from the database"""
    # Check if user is admin
    if not request.user.is_admin_user():
        messages.error(request, 'You do not have permission to perform this action.')
        return redirect('home')
    
    item = get_object_or_404(Item, id=item_id, is_archived=True)
    
    if request.method == 'POST':
        item_title = item.title
        item.delete()
        
        messages.success(request, f'Item "{item_title}" has been permanently deleted.')
        
        # Handle AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Item permanently deleted'})
        
        return redirect('admin_archived')
    
    # GET request - shouldn't happen normally, redirect to archived
    return redirect('admin_archived')


@login_required
def admin_archived_items_view(request):
    """View all archived items"""
    # Check if user is admin
    if not request.user.is_admin_user():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')
    
    # Get filter parameters
    item_type_filter = request.GET.get('type', '')
    reason_filter = request.GET.get('reason', '')
    search_query = request.GET.get('search', '')
    
    # Get all archived items for stats (before filtering)
    all_archived = Item.objects.filter(is_archived=True)
    total_archived = all_archived.count()
    spam_count = all_archived.filter(archive_reason='spam').count()
    inappropriate_count = all_archived.filter(archive_reason='inappropriate').count()
    duplicate_count = all_archived.filter(archive_reason='duplicate').count()
    resolved_count = all_archived.filter(archive_reason='resolved').count()
    other_count = all_archived.filter(archive_reason='other').count()
    resolved_other_count = resolved_count + other_count
    
    # Get archived items for display
    archived_items = all_archived.select_related('posted_by', 'archived_by').order_by('-archived_at')
    
    # Apply filters
    if item_type_filter:
        archived_items = archived_items.filter(item_type=item_type_filter)
    if reason_filter:
        archived_items = archived_items.filter(archive_reason=reason_filter)
    if search_query:
        archived_items = archived_items.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(posted_by__email__icontains=search_query)
        )
    
    # Pagination
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    paginator = Paginator(archived_items, 10)
    page = request.GET.get('page')
    
    try:
        items_page = paginator.page(page)
    except PageNotAnInteger:
        items_page = paginator.page(1)
    except EmptyPage:
        items_page = paginator.page(paginator.num_pages)
    
    # Get pending items count for navbar badge
    pending_count = Item.objects.filter(status='pending', is_archived=False).count()
    
    context = {
        'items': items_page,
        'total_archived': total_archived,
        'spam_count': spam_count,
        'inappropriate_count': inappropriate_count,
        'duplicate_count': duplicate_count,
        'resolved_other_count': resolved_other_count,
        'item_type_filter': item_type_filter,
        'reason_filter': reason_filter,
        'search_query': search_query,
        'pending_count': pending_count,
        'archive_reasons': Item.ARCHIVE_REASON_CHOICES,
    }
    
    return render(request, 'lfapp/admin_archived.html', context)

