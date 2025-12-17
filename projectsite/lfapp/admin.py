from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.utils import timezone

from .models import CustomUser, Item, Claim, Notification


"""PSU or PalSu?"""
"""/admin"""
@admin.register(CustomUser) 
class CustomUserAdmin(UserAdmin): # shortcut for admin.site.register()
    """Custom User Admin with exten fields"""
    list_display = [
        'email', 'username', 'role', 'is_verified',
        'is_psu_user', 'is_active', 'date_joined'
    ]
    list_filter = ['role', 'is_verified', 'is_active', 'is_staff', 'date_joined']
    search_fields = ['email', 'username', 'student_id', 'first_name', 'last_name']
    ordering = ['-date_joined']

    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'is_verified', 'phone_number', 'student_id', 'profile_picture')
        }),
    )

    readonly_fields = ['date_joined', 'last_login']

    def is_psu_user(self, obj):
        """Display PSU User status with green or red stat color"""
        if obj.is_psu_user():
            return format_html('<span style="color: green;">✓ Yes</span>')
        return format_html('<span style="color: red;"> ✗ No</span>')
    is_psu_user.short_description = 'PSU User'

    actions = ['verify_users', 'unverify_users', 'make_verified_role', 'make_admin_role']

    def verify_users(self, request, queryset):
        """Verify selected users"""
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} user(s) verified successfully.')
    verify_users.short_description = 'Verify selected users'

    def unverify_users(self, request, queryset): 
        """Unverify selected users"""
        updated = queryset.update(is_verified=False)
        self.message_user(request, f'{updated} user(s) unverified successfully.')
    unverify_users.short_description = 'Unverify selected users'

    def make_verified_role(self, request, queryset):
        """Change role to verified"""
        updated = queryset.update(role='verified')
        self.message_user(request, f'{updated} user(s) role changed to Verified.')
    make_verified_role.short_description = 'Change role to Verified'

    def make_admin_role(self, request, queryset):
        """Change role to admin"""
        updated = queryset.update(role='admin')
        self.message_user(request, f'{updated} user(s) role change to Admin role')
    make_admin_role.short_description = 'Change role to Admin'


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    """Item Admin with filtering and actions"""
    list_display = [
        'title', 'item_type', 'status', 'category',
        'posted_by', 'created_at', 'approved_by', 'claimed_by', 'has_image'
    ]
    list_filter = ['item_type', 'status', 'category', 'created_at', 'date_found', 'date_lost', 'claimed_at']
    search_fields = ['title', 'description', 'location_found', 'location_lost', 'posted_by__email', 'claimed_by__email']
    readonly_fields = ['created_at', 'updated_at', 'approved_at', 'claimed_at', 'image_preview']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'


    fieldsets = (
    ('Item Information', {
        'fields': ('title', 'description', 'item_type', 'category', 'image', 'image_preview')
    }),
    ('Location & Date', {
        'fields': ('location_found', 'location_lost', 'date_found', 'date_lost')
    }),
    ('Status & Approval', {
        'fields': ('status', 'posted_by', 'display_name', 'approved_by', 'approved_at') # approved_at = date and time
    }),
    ('Claim Information', {
        'fields': ('claimed_by', 'claimed_at'),
        'classes': ('collapse',)
    }),
    ('Timestamps', {
        'fields': ('created_at', 'updated_at'),
        'classes': ('collapse',)
    }),
)

    def has_image(self, obj):
        """Display kung may image"""
        if obj.image:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: red;">✗</span>')
    has_image.short_description = 'Image'

    def image_preview(self, obj):
        """Display image prev in Admin"""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 200px;" />',
                obj.image.url
            )
        return "No image"
    image_preview.short_description = 'Image Preview'

    actions = ['approve_items', 'reject_items', 'mark_as_claimed']

    def approve_items(self, request, queryset):
        """Approve selected items"""
        updated = queryset.filter(status='pending').update(
            status='approved',
            approved_by=request.user,
            approved_at=timezone.now()
        )
        self.message_user(request, f'{updated} item(s) approved.')
    approve_items.short_description = 'Approve selected items'

    def reject_items(self, request, queryset):
        """Reject selected items"""
        updated = queryset.filter(status='pending').update(
            status='rejected',
            approved_by=request.user,
            approved_at=timezone.now()
        )
        self.message_user(request, f'{updated} item(s) rejected.')
    reject_items.short_description = 'Reject selected items'

    def mark_as_claimed(self, request, queryset):
        """Mark items as claimed"""
        updated = queryset.filter(status='approved').update(
            status='claimed',
            claimed_by=request.user,
            claimed_at=timezone.now()
        )
        self.message_user(request, f'{updated} item(s) marked as claimed.')
    mark_as_claimed.short_description = 'Mark as claimed'

@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    """Claim Admin with filtering and actions"""
    list_display = [
        'item', 'claimed_by', 'status', 'created_at',
        'resolved_by', 'resolved_at'
    ]
    list_filter = ['status', 'created_at', 'resolved_at']
    search_fields = [
        'item__title', 'claimed_by__email',
        'claim_message', 'contact_info'
    ]
    readonly_fields = ['created_at', 'updated_at', 'resolved_at']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Claim Information', {
            'fields': ('item', 'claimed_by', 'claim_message', 'contact_info')
        }),
        ('Status', {
            'fields': ('status', 'resolved_by', 'resolved_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['approve_claims', 'reject_claims']

    def approve_claims(self, request, queryset):
        """Approve selected clams"""
        updated = 0
        for claim in queryset.filter(status='pending'):
            claim.status = 'approved'
            claim.resolved_by = request.user
            claim.resolved_at = timezone.now()
            claim.save()

            #Mark item as claimed
            claim.item.status = 'claimed'
            claim.item.save()
            updated += 1

        self.message_user(request, f'{updated} claim(s) approved. ')
    approve_claims.short_description = 'Approve selected claims'

    def reject_claims(self, request, queryset):
        """Reject selected claims"""
        updated = queryset.filter(status='pending').update(
            status='rejected',
            resolved_by=request.user,
            resolved_at=timezone.now()
        )
        self.message_user(request, f'{updated} claim(s) rejected.')
    reject_claims.short_description = 'Reject selected claims'

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Notification ADmin"""
    list_display = [
        'user', 'notification_type', 'is_read',
        'item', 'claim', 'created_at'
    ]
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__email', 'message']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Notification Details', {
            'fields': ('user', 'notification_type', 'message', 'is_read')
        }),
        ('Related Objects', {
            'fields': ('item', 'claim')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_as_read', 'mark_as_unread']

    def mark_as_read(self, request, queryset):
        """Mark notifications as read"""
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} notification(s) marked as read.')
    mark_as_read.short_description = 'Mark as read'

    def mark_as_unread(self, request, queryset):
        """Mark notifications as unread"""
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} notification(s) marked as unread.')
    mark_as_unread.short_description = 'Mark as unread'






