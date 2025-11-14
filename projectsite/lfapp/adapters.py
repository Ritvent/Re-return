from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.core.exceptions import ValidationError
from django.contrib import messages
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.shortcuts import get_current_site


class PSUEmailAdapter(DefaultAccountAdapter):
    """
    Custom adapter to restrict signups to @psu.palawan.edu.ph emails only
    """
    
    def clean_email(self, email):
        """
        Validate that the email belongs to PSU domain
        """
        email = super().clean_email(email)
        
        if not email.endswith('@psu.palawan.edu.ph'):
            raise ValidationError(
                'Only PSU Palawan email addresses (@psu.palawan.edu.ph) are allowed to register.'
            )
        
        return email
    
    def save_user(self, request, user, form, commit=True):
        """
        Save user with additional PSU-specific logic
        """
        user = super().save_user(request, user, form, commit=False)
        
        # Set verified users with PSU email as 'verified' role
        if user.email.endswith('@psu.palawan.edu.ph'):
            user.role = 'verified'
            user.is_verified = True
        
        if commit:
            user.save()
        
        return user


class PSUSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom social account adapter to restrict Google OAuth to PSU domain
    """
    
    def get_app(self, request, provider, client_id=None):
        """
        Override to fix MultipleObjectsReturned issue.
        Uses .distinct() to handle cases where app is linked to multiple sites.
        """
        try:
            site = get_current_site(request)
            queryset = SocialApp.objects.filter(provider=provider)
            
            if client_id:
                queryset = queryset.filter(client_id=client_id)
            
            # Filter by current site and use distinct() to avoid duplicates
            queryset = queryset.filter(sites__id=site.id).distinct()
            
            return queryset.get()
        except SocialApp.DoesNotExist:
            # Fall back to the default implementation
            return super().get_app(request, provider, client_id)
    
    def pre_social_login(self, request, sociallogin):
        """
        Invoked after a user successfully authenticates via a social provider,
        but before the login is actually processed.
        """
        # Get the email from the social account
        email = sociallogin.account.extra_data.get('email', '')
        
        # Check if email is from PSU domain
        if not email.endswith('@psu.palawan.edu.ph'):
            messages.error(
                request,
                'Only PSU Palawan email addresses (@psu.palawan.edu.ph) are allowed. '
                'Please sign in with your PSU email.'
            )
            # Prevent the login
            raise ValidationError('Invalid email domain')
    
    def populate_user(self, request, sociallogin, data):
        """
        Populate user instance with data from social account
        """
        user = super().populate_user(request, sociallogin, data)
        
        # Set PSU users as verified
        if user.email and user.email.endswith('@psu.palawan.edu.ph'):
            user.role = 'verified'
            user.is_verified = True
        
        # Ensure unique username by using email as username
        if user.email:
            user.username = user.email
        
        return user
    
    def generate_unique_username(self, txts, regex=None):
        """
        Generate a unique username from email.
        Override to use email directly as username.
        """
        from allauth.account.models import EmailAddress
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        # Try to get email from txts
        email = None
        for txt in txts:
            if '@' in txt:
                email = txt
                break
        
        if email:
            # Check if username (email) already exists
            if not User.objects.filter(username=email).exists():
                return email
            
            # If email exists as username, the user already has an account
            # This shouldn't happen with proper social account setup
            # but as fallback, use email prefix with incrementing number
            base = email.split('@')[0]
            username = base
            i = 1
            while User.objects.filter(username=username).exists():
                username = f"{base}{i}"
                i += 1
            return username
        
        # Fallback to default implementation
        return super().generate_unique_username(txts, regex)
