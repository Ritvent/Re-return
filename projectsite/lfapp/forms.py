from django import forms
from .models import Item
from datetime import date


class ItemForm(forms.ModelForm):
    """Form for posting lost and found items"""
    
    class Meta:
        model = Item
        fields = [
            'title', 'description', 'category', 'location_found', 
            'location_lost', 'date_found', 'date_lost', 'image', 'display_name'
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
                'max': date.today().isoformat()
            }),
            'date_lost': forms.DateInput(attrs={
                'class': 'w-full px-4 py-2 rounded-md border border-input bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring',
                'type': 'date',
                'max': date.today().isoformat()
            }),
            'image': forms.FileInput(attrs={
                'class': 'w-full px-4 py-2 rounded-md border border-input bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring',
                'accept': 'image/*'
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
            'display_name': 'Display my name publicly'
        }

    def __init__(self, *args, **kwargs):
        self.item_type = kwargs.pop('item_type', None)
        super().__init__(*args, **kwargs)
        
        # Image is always optional (not required when editing)
        self.fields['image'].required = False
        
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

    def clean(self):
        cleaned_data = super().clean()
        
        # Validate that the date is not in the future
        if self.item_type == 'lost' and cleaned_data.get('date_lost'):
            if cleaned_data['date_lost'] > date.today():
                self.add_error('date_lost', 'Date cannot be in the future')
        
        if self.item_type == 'found' and cleaned_data.get('date_found'):
            if cleaned_data['date_found'] > date.today():
                self.add_error('date_found', 'Date cannot be in the future')
        
        # Validate display_name is checked for found items
        if self.item_type == 'found' and not cleaned_data.get('display_name'):
            self.add_error('display_name', 'You must agree to display your name for found items')
        
        return cleaned_data
