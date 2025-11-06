"""
Forms for managing site logos with SVG support.
"""
from django import forms
from django.core.exceptions import ValidationError
from .models import SiteLogo
import xml.etree.ElementTree as ET


def validate_svg_file(file):
    """
    Validate that uploaded SVG file is safe and well-formed.
    """
    if file.name.lower().endswith('.svg'):
        try:
            # Read file content
            file.seek(0)
            content = file.read()
            if isinstance(content, bytes):
                content = content.decode('utf-8')
            
            # Check for potentially dangerous content
            dangerous_tags = ['script', 'object', 'embed', 'iframe']
            content_lower = content.lower()
            for tag in dangerous_tags:
                if f'<{tag}' in content_lower:
                    raise ValidationError(
                        f'SVG file contains potentially dangerous <{tag}> tag. '
                        'Please remove it and try again.'
                    )
            
            # Validate XML structure
            try:
                ET.fromstring(content)
            except ET.ParseError as e:
                raise ValidationError(f'Invalid SVG file: {str(e)}')
            
            # Reset file pointer
            file.seek(0)
            
        except UnicodeDecodeError:
            raise ValidationError('SVG file must be UTF-8 encoded.')
        except Exception as e:
            if not isinstance(e, ValidationError):
                raise ValidationError(f'Error validating SVG file: {str(e)}')
            raise


class SiteLogoAdminForm(forms.ModelForm):
    """
    Admin form for SiteLogo model with SVG support.
    """
    
    class Meta:
        model = SiteLogo
        fields = '__all__'
        widgets = {
            'alt_text': forms.TextInput(attrs={'placeholder': 'e.g., BishulSheli Logo'}),
        }
    
    def clean_image_file(self):
        """Validate uploaded file"""
        image_file = self.cleaned_data.get('image_file')
        
        if image_file:
            # Check file size (max 5MB)
            if image_file.size > 5 * 1024 * 1024:
                raise ValidationError('File size must be under 5MB.')
            
            # Validate SVG files
            if image_file.name.lower().endswith('.svg'):
                validate_svg_file(image_file)
            
        return image_file


class BulkLogoUploadForm(forms.Form):
    """
    Form for bulk logo uploads via Quick Setup.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Create fields dynamically for each logo type and language
        logo_types = [
            ('navbar_desktop', 'Navbar Desktop'),
            ('navbar_mobile', 'Navbar Mobile'),
            ('login_page', 'Login Page'),
            ('favicon', 'Favicon'),
            ('app_icon', 'App Icon'),
        ]
        
        languages = [('en', 'English'), ('ru', 'Russian'), ('he', 'Hebrew')]
        
        for logo_type, logo_label in logo_types:
            for lang_code, lang_label in languages:
                field_name = f'{logo_type}_{lang_code}'
                self.fields[field_name] = forms.FileField(
                    required=False,
                    label=f'{logo_label} ({lang_label})',
                    help_text='SVG recommended (max 5MB)',
                    widget=forms.FileInput(attrs={'accept': '.svg,.png,.jpg,.jpeg,.webp,.ico'})
                )
    
    def clean(self):
        """Validate all uploaded files"""
        cleaned_data = super().clean()
        
        for field_name, file in cleaned_data.items():
            if file:
                # Check file size
                if file.size > 5 * 1024 * 1024:
                    self.add_error(field_name, 'File size must be under 5MB.')
                
                # Validate SVG files
                if file.name.lower().endswith('.svg'):
                    try:
                        validate_svg_file(file)
                    except ValidationError as e:
                        self.add_error(field_name, e.message)
        
        return cleaned_data


