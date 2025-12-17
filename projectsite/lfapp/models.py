from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import EmailValidator # Validator for email field
from django.core.exceptions import ValidationError

class TimeStampedModel(models.Model):
    """ Will be inherited by all"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

def validate_psu_email(value):
    """ Check email if ends with @psu.palawan.edu.ph"""
    if not value.endswith('@psu.palawan.edu.ph'):
        raise ValidationError(
            'Be gone outsider'
        )
    

class CustomUser(AbstractUser):
    """ 3 roels, public, verified, admin"""
    ROLE_CHOICES = (
        ('public', 'Public User'), 
        ('verified', 'Verified User'),
        ('admin', 'Admin'),
    )

    email = models.EmailField(
        unique=True,
        validators=[EmailValidator()]
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='public')
    is_verified = models.BooleanField(
        default=False,
        help_text='Email verification status'
    )
    phone_number = models.CharField(max_length=20, blank=True, default='')
    student_id = models.CharField(max_length=50, blank=True, default='')
    profile_picture = models.ImageField(
        upload_to='profiles/', 
        blank=True, 
        null=True
    )
    google_profile_picture = models.URLField(
        max_length=500, 
        blank=True, 
        default='',
        help_text='Profile picture URL from Google'
    )
    

    USERNAME_FIELD = 'email' # unique id 
    REQUIRED_FIELDS = ['username']  # username is still required

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.email
    
    def is_psu_user(self):
        """Check if user has a verified psu email"""
        return (
            self.is_verified and
            self.email.endswith('@psu.palawan.edu.ph')
        )
    
    @property
    def has_psu_email(self):
        """Check if user has a psu email (regardless of verification)"""
        return self.email.endswith('@psu.palawan.edu.ph')
    
    def can_post_items(self):
        """Check if user can post items"""
        return self.is_verified and self.role in ['verified', 'admin']
    
    def is_admin_user(self):
        """Check if user is admin"""
        return self.role == 'admin' or self.is_superuser
    
    def clean(self):
        """Validate psu email only for verified/admin roles"""
        super().clean()
        if self.role in ['verified', 'admin']:
            validate_psu_email(self.email)

    @property
    def email_username(self):
        """number only before the @"""
        if self.email:
            return self.email.split('@')[0]
        return self.username

"""Items"""

class Item(TimeStampedModel):
    """POST Lost and Found Items"""
    ITEM_TYPE_CHOICES = [
        ('lost', 'Lost Item'),
        ('found', 'Found Item'),
    ]
    
    """add lang kayo if may naisip pa"""
    CATEGORY_CHOICES = [
        ('electronics', 'Electronics (Phone, Laptop, etc.)'),
        ('accessories', 'Accessories (Wallet, Watch, etc.)'),
        ('documents', 'Documents/IDs'),
        ('clothing', 'Clothing & Wearables'),
        ('bags', 'Bags & Backpacks'),
        ('keys', 'Keys & Keychains'),
        ('books', 'Books & School Supplies'),
        ('sports', 'Sports Equipment'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('claimed', 'Claimed'),
        ('found', 'Found/Recovered'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    item_type = models.CharField(max_length=10, choices=ITEM_TYPE_CHOICES) # lost or found
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='other',
        help_text='Item category for easier filtering' 
    )
    location_found = models.CharField(
        max_length=200,
        blank=True,
        default='',
        help_text='Where the item was found'
    )
    location_lost = models.CharField(
        max_length=200,
        blank=True,
        default='',
        help_text='Where do you think you lost the item'
    )
    date_found = models.DateField(blank=True, null=True)
    date_lost = models.DateField(blank=True, null=True)
    image = models.ImageField(upload_to='item_images/', blank=True, null=True)
    contact_number = models.CharField(
        max_length=20,
        blank=True,
        default='',
        help_text='Optional contact number for this item'
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    posted_by = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='posted_items'
    )
    display_name = models.BooleanField(
        default=False,
        help_text='Display poster name publicly (required for found items)'
    )
    approved_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_items'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    claimed_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='claimed_items',
        help_text='User who claimed this item'
    )
    claimed_at = models.DateTimeField(null=True, blank=True, help_text='When the item was claimed')
    completion_name = models.CharField(
        max_length=200,
        blank=True,
        default='',
        help_text='Name of person who claimed (for found items) or returned (for lost items) the item'
    )
    completion_email = models.EmailField(
        blank=True,
        default='',
        help_text='Email of person who claimed or returned the item'
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the item was marked as found/claimed by the poster'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether the item is listed publicly (users can delist their posts)'
    )
    content_updated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the item content was last edited by the poster'
    )
    
    # Admin archive fields
    ARCHIVE_REASON_CHOICES = [
        ('spam', 'Spam'),
        ('inappropriate', 'Inappropriate content'),
        ('duplicate', 'Duplicate post'),
        ('resolved', 'Resolved/No longer needed'),
        ('other', 'Other'),
    ]
    
    is_archived = models.BooleanField(
        default=False,
        help_text='Whether the item was archived/deleted by admin'
    )
    archived_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='archived_items',
        help_text='Admin who archived this item'
    )
    archived_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the item was archived by admin'
    )
    archive_reason = models.CharField(
        max_length=20,
        choices=ARCHIVE_REASON_CHOICES,
        blank=True,
        default='',
        help_text='Reason for archiving'
    )
    archive_notes = models.TextField(
        blank=True,
        default='',
        help_text='Additional notes about why item was archived'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Item'
        verbose_name_plural = 'Items'

    def __str__(self):
        return f"({self.get_item_type_display()}: {self.title})"
    
    def can_be_deleted(self):
        """Only non-completed items can be deleted - completed items are success stories"""
        return self.status not in ['claimed', 'found']
    
    def can_be_delisted(self):
        """Only non-completed items can be delisted - completed items must remain visible"""
        return self.status not in ['claimed', 'found']

    def get_claimant_picture(self):
        """
        Get the profile picture of the person who claimed/returned the item.
        Prioritizes claimed_by relationship, then falls back to looking up user by completion_email.
        """
        # 1. Check claimed_by relationship
        if self.claimed_by and self.claimed_by.google_profile_picture:
            return self.claimed_by.google_profile_picture
        
        # 2. Check completion_email
        if self.completion_email:
            try:
                user = CustomUser.objects.get(email=self.completion_email)
                if user.google_profile_picture:
                    return user.google_profile_picture
            except CustomUser.DoesNotExist:
                pass
        
        return None
    
"""Reclaim, Recover"""
class Claim(TimeStampedModel):
    """ Claims made on items"""

    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='claims')
    claimed_by = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='claims'
    )
    claim_message = models.TextField(
        help_text='Describe why you believe this is your item' #la maisip
    )
    contact_info = models.CharField(
        max_length=200,
        help_text='Additional contact information'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_claims',
        help_text='Admin who resolved the claim'
    )

    class Meta:
        ordering = ['-created_at']
        unique_together = ('item', 'claimed_by') # One claim per user per item dapat
        verbose_name = 'Claim'
        verbose_name_plural = 'Claims'


    def __str__(self):
        return f"Claim by {self.claimed_by.email} on {self.item.title}"
    
class Notification(TimeStampedModel):
    """Notifs for users"""
    NOTIFICATION_TYPES = [
        ('item_approved', 'Item Approved'),
        ('item_rejected', 'Item Rejected'),
        ('claim_received', 'New Claim Received'),
        ('claim_approved', 'Claim Approved'),
        ('claim_rejected', 'Claim Rejected'),
    ]

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    message = models.TextField()
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    claim = models.ForeignKey(
        Claim,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )

    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
    
    def __str__(self):
        return f"{self.user.email} - {self.get_notification_type_display()}"

class ContactMessage(TimeStampedModel):
    """In-app messaging for contacting item posters"""
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name='contact_messages',
        help_text='The item this message is about'
    )
    sender = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        help_text='User who sent the message'
    )
    recipient = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='received_messages',
        help_text='User who receives the message'
    )
    subject = models.CharField(max_length=200, help_text='Message subject')
    message = models.TextField(help_text='Message content')
    sender_phone = models.CharField(
        max_length=20,
        blank=True,
        default='',
        help_text='Optional contact phone number'
    )
    image = models.ImageField(
        upload_to='message_images/',
        blank=True,
        null=True,
        help_text='Optional image attachment'
    )
    parent_message = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        help_text='Parent message if this is a reply'
    )
    is_read = models.BooleanField(default=False, help_text='Has recipient read this message')
    is_deleted = models.BooleanField(default=False, help_text='Has sender deleted this message')
    
    # Soft delete tracking - per-user deletion
    deleted_by_sender = models.BooleanField(
        default=False,
        help_text='Has sender deleted this thread from their view'
    )
    deleted_by_recipient = models.BooleanField(
        default=False,
        help_text='Has recipient deleted this thread from their view'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Contact Message'
        verbose_name_plural = 'Contact Messages'
    
    def __str__(self):
        return f"Message from {self.sender.email} to {self.recipient.email} about {self.item.title}"
    
    def get_thread_messages(self):
        """Get all messages in this conversation thread"""
        if self.parent_message:
            root = self.parent_message
        else:
            root = self
        
        # Get root message and all its replies
        return ContactMessage.objects.filter(
            models.Q(id=root.id) | models.Q(parent_message=root)
        ).order_by('created_at')




    



