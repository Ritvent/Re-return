from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.core.paginator import Paginator
from .models import Item, CustomUser
from .forms import ItemForm

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
        status='approved'
    ).select_related('posted_by').order_by('-created_at')[:3]
    
    # Get recent found items (limit to 3)
    recent_found = Item.objects.filter(
        item_type='found',
        status='approved'
    ).select_related('posted_by').order_by('-created_at')[:3]
    
    # Get recent claimed items (limit to 5)
    recent_claimed = Item.objects.filter(
        status='claimed'
    ).select_related('posted_by', 'claimed_by').order_by('-claimed_at')[:5]
    
    context = {
        'recent_lost': recent_lost,
        'recent_found': recent_found,
        'recent_claimed': recent_claimed,
    }
    
    return render(request, 'lfapp/home.html', context)

def lost_items_view(request):
    """View all lost items with search and filter - Public access allowed"""
    items = Item.objects.filter(
        item_type='lost',
        status='approved'
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
    items = Item.objects.filter(
        item_type='found',
        status='approved'
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
    
    context = {
        'all_items': all_items,
        'total_items': total_items,
        'lost_count': lost_count,
        'found_count': found_count,
        'lost_percentage': int(lost_percentage),
        'found_percentage': int(found_percentage),
        'category_count': category_count,
    }
    
    return render(request, 'lfapp/admin_dashboard.html', context)

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
    """View all claimed items - Public access allowed"""
    items = Item.objects.filter(
        status='claimed'
    ).select_related('posted_by', 'claimed_by').order_by('-claimed_at')
    
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
            if not request.user.is_admin_user():
                updated_item.status = 'pending'  # Needs re-approval after edit
            updated_item.save()
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
    
    received_messages = ContactMessage.objects.filter(
        recipient=request.user
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
    
    sent_messages = ContactMessage.objects.filter(
        sender=request.user
    ).select_related('recipient', 'item').order_by('-created_at')
    
    context = {
        'messages': sent_messages,
    }
    return render(request, 'lfapp/messages_sent.html', context)

