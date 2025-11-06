"""
Forms for Legal Compliance app.
"""
from django import forms
from .models import LegalDocument, AboutPage


class LegalDocumentUploadForm(forms.Form):
    """
    Form for uploading legal documents from markdown files.
    Allows bulk upload of multiple documents at once.
    """
    DOCUMENT_TYPE_CHOICES = LegalDocument.DOCUMENT_TYPES
    LANGUAGE_CHOICES = LegalDocument.LANGUAGE_CHOICES

    document_type = forms.ChoiceField(
        choices=DOCUMENT_TYPE_CHOICES,
        label='Document Type',
        help_text='Select the type of legal document'
    )
    language_code = forms.ChoiceField(
        choices=LANGUAGE_CHOICES,
        label='Language',
        initial='en',
        help_text='Select document language'
    )
    version = forms.CharField(
        max_length=20,
        label='Version',
        initial='2.0',
        help_text='Document version (e.g., 2.0, 2.1)'
    )
    effective_date = forms.DateField(
        label='Effective Date',
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text='Date when this version becomes effective'
    )
    markdown_file = forms.FileField(
        label='Markdown File',
        help_text='Upload a .md file with the document content',
        widget=forms.FileInput(attrs={'accept': '.md,.markdown,.txt'})
    )
    is_active = forms.BooleanField(
        label='Set as Active Version',
        initial=True,
        required=False,
        help_text='Automatically deactivate other versions of this document'
    )

    def clean_markdown_file(self):
        """Validate the uploaded file"""
        file = self.cleaned_data.get('markdown_file')
        
        if file:
            # Check file extension
            if not file.name.lower().endswith(('.md', '.markdown', '.txt')):
                raise forms.ValidationError('Only .md, .markdown, or .txt files are allowed')
            
            # Check file size (max 5MB)
            if file.size > 5 * 1024 * 1024:
                raise forms.ValidationError('File size must not exceed 5MB')
            
            # Try to decode as UTF-8
            try:
                content = file.read().decode('utf-8')
                file.seek(0)  # Reset file pointer
                
                # Basic validation - ensure it's not empty
                if not content.strip():
                    raise forms.ValidationError('File is empty')
                    
            except UnicodeDecodeError:
                raise forms.ValidationError('File must be UTF-8 encoded')
        
        return file


class LegalDocumentAdminForm(forms.ModelForm):
    """
    Enhanced admin form for legal documents with optional file upload.
    """
    markdown_file = forms.FileField(
        label='Upload Markdown File (Optional)',
        required=False,
        help_text='Upload a .md file to replace the content below',
        widget=forms.FileInput(attrs={'accept': '.md,.markdown,.txt'})
    )

    class Meta:
        model = LegalDocument
        fields = '__all__'
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 30,
                'style': 'font-family: monospace; font-size: 13px;'
            })
        }

    def __init__(self, *args, **kwargs):
        """Make content field not required initially"""
        super().__init__(*args, **kwargs)
        # Make content not required (we'll validate in clean())
        self.fields['content'].required = False

    def clean(self):
        """Process the uploaded file if provided and validate content"""
        cleaned_data = super().clean()
        markdown_file = cleaned_data.get('markdown_file')
        content = cleaned_data.get('content')
        
        if markdown_file:
            try:
                # Read the file content
                file_content = markdown_file.read().decode('utf-8')
                
                # Validate file is not empty
                if not file_content.strip():
                    raise forms.ValidationError('Uploaded file is empty')
                
                # Replace the content field with file content
                cleaned_data['content'] = file_content
                
            except UnicodeDecodeError:
                raise forms.ValidationError('File must be UTF-8 encoded')
        elif not content or not content.strip():
            # If no file and no content, raise error
            raise forms.ValidationError('Either upload a file or provide content in the text area')
        
        return cleaned_data


class AboutPageAdminForm(forms.ModelForm):
    """
    Enhanced admin form for About page content with optional file upload.
    """
    markdown_file = forms.FileField(
        label='Upload Markdown File (Optional)',
        required=False,
        help_text='Upload a .md file to replace the content below',
        widget=forms.FileInput(attrs={'accept': '.md,.markdown,.txt'})
    )

    class Meta:
        model = AboutPage
        fields = '__all__'
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 30,
                'style': 'font-family: monospace; font-size: 13px;'
            }),
            'meta_description': forms.Textarea(attrs={
                'rows': 3,
                'style': 'font-size: 13px;'
            })
        }

    def __init__(self, *args, **kwargs):
        """Make content field not required initially"""
        super().__init__(*args, **kwargs)
        # Make content not required (we'll validate in clean())
        self.fields['content'].required = False

    def clean(self):
        """Process the uploaded file if provided and validate content"""
        cleaned_data = super().clean()
        markdown_file = cleaned_data.get('markdown_file')
        content = cleaned_data.get('content')
        
        if markdown_file:
            try:
                # Read the file content
                file_content = markdown_file.read().decode('utf-8')
                
                # Validate file is not empty
                if not file_content.strip():
                    raise forms.ValidationError('Uploaded file is empty')
                
                # Replace the content field with file content
                cleaned_data['content'] = file_content
                
            except UnicodeDecodeError:
                raise forms.ValidationError('File must be UTF-8 encoded')
        elif not content or not content.strip():
            # If no file and no content, raise error
            raise forms.ValidationError('Either upload a file or provide content in the text area')
        
        return cleaned_data

