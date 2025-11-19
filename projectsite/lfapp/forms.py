from django import forms
from .models import Item
from datetime import date
import re


class ItemForm(forms.ModelForm):
    """Form for posting lost and found items"""
    
    class Meta:
        model = Item
        fields = [
            'title', 'description', 'category', 'location_found', 
            'location_lost', 'date_found', 'date_lost', 'image', 'contact_number', 'display_name'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 rounded-md border border-input bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring',
                'placeholder': 'e.g., Blue Backpack, iPhone 14, Car Keys'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 rounded-md border border-input bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring',
                'placeholder': 'Provide detailed description including color, brand, distinctive features...',
                'rows': 4
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-4 py-2 rounded-md border border-input bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring'
            }),
            'location_found': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 rounded-md border border-input bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring',
                'placeholder': 'e.g., University Library, Student Center, Building A'
            }),
            'location_lost': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 rounded-md border border-input bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring',
                'placeholder': 'e.g., University Library, Student Center, Building A'
            }),
            'date_found': forms.DateInput(attrs={
                'class': 'w-full px-4 py-2 rounded-md border border-input bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring',
                'type': 'date',
                'min': '2025-01-01',
                'max': date.today().isoformat()
            }),
            'date_lost': forms.DateInput(attrs={
                'class': 'w-full px-4 py-2 rounded-md border border-input bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring',
                'type': 'date',
                'min': '2025-01-01',
                'max': date.today().isoformat()
            }),
            'image': forms.FileInput(attrs={
                'class': 'w-full px-4 py-2 rounded-md border border-input bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring',
                'accept': 'image/*'
            }),
            'contact_number': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 rounded-md border border-input bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring',
                'type': 'tel',
                'placeholder': 'e.g., +63 912 345 6789',
                'pattern': '[0-9+\-\s()]*',
                'title': 'Only numbers, +, -, spaces, and parentheses are allowed'
            }),
            'display_name': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 rounded border-input text-primary focus:ring-2 focus:ring-ring'
            })
        }
        labels = {
            'title': 'Item Name',
            'description': 'Description',
            'category': 'Category',
            'location_found': 'Location Found',
            'location_lost': 'Location Lost',
            'date_found': 'Date Found',
            'date_lost': 'Date Lost',
            'image': 'Image (Optional)',
            'contact_number': 'Contact Number (Optional)',
            'display_name': 'Display my name publicly'
        }

    def __init__(self, *args, **kwargs):
        self.item_type = kwargs.pop('item_type', None)
        super().__init__(*args, **kwargs)
        
        # Image and contact number are always optional
        self.fields['image'].required = False
        self.fields['contact_number'].required = False
        
        # Make only relevant fields required based on item_type
        if self.item_type == 'lost':
            self.fields['location_lost'].required = True
            self.fields['date_lost'].required = True
            self.fields['location_found'].required = False
            self.fields['date_found'].required = False
            # Remove found fields from form
            del self.fields['location_found']
            del self.fields['date_found']
            # Display name is optional for lost items
            self.fields['display_name'].required = False
            self.fields['display_name'].help_text = 'Optional: Show your name on the listing'
        elif self.item_type == 'found':
            self.fields['location_found'].required = True
            self.fields['date_found'].required = True
            self.fields['location_lost'].required = False
            self.fields['date_lost'].required = False
            # Remove lost fields from form
            del self.fields['location_lost']
            del self.fields['date_lost']
            # Display name is mandatory for found items
            self.fields['display_name'].required = True
            self.fields['display_name'].initial = True
            self.fields['display_name'].help_text = 'Required: Your name will be displayed as "Found by [Your Name]"'

    def clean_contact_number(self):
        """Validate contact number contains only allowed characters"""
        contact_number = self.cleaned_data.get('contact_number', '')
        if contact_number:
            # Allow only numbers, +, -, spaces, and parentheses
            if not re.match(r'^[0-9+\-\s()]+$', contact_number):
                raise forms.ValidationError('Contact number can only contain numbers, +, -, spaces, and parentheses')
        return contact_number
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validate that the date is not in the future and not before 2025
        if self.item_type == 'lost' and cleaned_data.get('date_lost'):
            if cleaned_data['date_lost'] > date.today():
                self.add_error('date_lost', 'Date cannot be in the future')
            elif cleaned_data['date_lost'] < date(2025, 1, 1):
                self.add_error('date_lost', 'Date must be from 2025 onwards')
        
        if self.item_type == 'found' and cleaned_data.get('date_found'):
            if cleaned_data['date_found'] > date.today():
                self.add_error('date_found', 'Date cannot be in the future')
            elif cleaned_data['date_found'] < date(2025, 1, 1):
                self.add_error('date_found', 'Date must be from 2025 onwards')
        
        # Validate display_name is checked for found items
        if self.item_type == 'found' and not cleaned_data.get('display_name'):
            self.add_error('display_name', 'You must agree to display your name for found items')
        
        return cleaned_data
