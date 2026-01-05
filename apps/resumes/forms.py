from django import forms
from django.forms import inlineformset_factory
from .models import *

class ResumeBasicForm(forms.ModelForm):
    """Step 1: Basic Information"""
    class Meta:
        model = Resume
        fields = [
            'title', 'full_name', 'email', 'phone', 'location',
            'linkedin_url', 'portfolio_url', 'github_url', 'summary'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Software Engineer Resume'
            }),
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'John Doe'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'john@example.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1 (555) 123-4567'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'San Francisco, CA'
            }),
            'linkedin_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://linkedin.com/in/yourprofile'
            }),
            'portfolio_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://yourportfolio.com'
            }),
            'github_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://github.com/yourusername'
            }),
            'summary': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Brief professional summary highlighting your key strengths and career objectives...'
            }),
        }


class ExperienceForm(forms.ModelForm):
    """Step 2: Work Experience"""
    class Meta:
        model = Experience
        fields = [
            'company', 'position', 'location', 'start_date', 
            'end_date', 'is_current', 'description', 'order'
        ]
        widgets = {
            'company': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Company Name'
            }),
            'position': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Job Title'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City, State'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'is_current': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': '• Achieved X by doing Y\n• Led team of Z to accomplish...'
            }),
            'order': forms.HiddenInput(),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        is_current = cleaned_data.get('is_current')
        end_date = cleaned_data.get('end_date')
        
        if is_current:
            cleaned_data['end_date'] = None
        elif not end_date and not is_current:
            raise forms.ValidationError("Please provide an end date or mark as current position.")
        
        return cleaned_data


class EducationForm(forms.ModelForm):
    """Step 3: Education"""
    class Meta:
        model = Education
        fields = [
            'institution', 'degree', 'field_of_study', 'location',
            'start_date', 'end_date', 'gpa', 'description', 'order'
        ]
        widgets = {
            'institution': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'University Name'
            }),
            'degree': forms.Select(attrs={'class': 'form-control'}),
            'field_of_study': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Computer Science'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City, State'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'gpa': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '3.8',
                'step': '0.01'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Honors, relevant coursework, achievements...'
            }),
            'order': forms.HiddenInput(),
        }


class SkillForm(forms.ModelForm):
    """Step 4: Skills"""
    class Meta:
        model = Skill
        fields = ['name', 'category', 'proficiency', 'order']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Python'
            }),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'proficiency': forms.Select(attrs={'class': 'form-control'}),
            'order': forms.HiddenInput(),
        }


class CertificationForm(forms.ModelForm):
    """Optional: Certifications"""
    class Meta:
        model = Certification
        fields = [
            'name', 'issuing_organization', 'issue_date', 
            'expiry_date', 'credential_id', 'credential_url', 'order'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'AWS Certified Solutions Architect'
            }),
            'issuing_organization': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Amazon Web Services'
            }),
            'issue_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'expiry_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'credential_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ABC123XYZ'
            }),
            'credential_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://verify.credential.com/xyz'
            }),
            'order': forms.HiddenInput(),
        }


class ProjectForm(forms.ModelForm):
    """Optional: Projects"""
    class Meta:
        model = Project
        fields = [
            'title', 'description', 'technologies', 
            'start_date', 'end_date', 'project_url', 'github_url', 'order'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'E-commerce Platform'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Built a full-stack e-commerce platform with...'
            }),
            'technologies': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Django, React, PostgreSQL, AWS'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'project_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://project-demo.com'
            }),
            'github_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://github.com/user/project'
            }),
            'order': forms.HiddenInput(),
        }


class TemplateSelectionForm(forms.ModelForm):
    """Step 5: Template Selection"""
    template = forms.ChoiceField(
        choices=Resume.TEMPLATE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'template-choice'}),
        label="Choose Your Template"
    )
    
    class Meta:
        model = Resume
        fields = ['template']


class ATSAnalysisForm(forms.Form):
    """ATS Optimization Tool"""
    job_description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 10,
            'placeholder': 'Paste the job description here...'
        }),
        label="Job Description",
        help_text="Paste the full job description to analyze your resume against."
    )


# Create Formsets for dynamic addition/removal
ExperienceFormSet = inlineformset_factory(
    Resume,
    Experience,
    form=ExperienceForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False
)

EducationFormSet = inlineformset_factory(
    Resume,
    Education,
    form=EducationForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False
)

SkillFormSet = inlineformset_factory(
    Resume,
    Skill,
    form=SkillForm,
    extra=3,
    can_delete=True,
    min_num=0,
    validate_min=False
)

CertificationFormSet = inlineformset_factory(
    Resume,
    Certification,
    form=CertificationForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False,
    can_delete_extra=True
)

ProjectFormSet = inlineformset_factory(
    Resume,
    Project,
    form=ProjectForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False,
    can_delete_extra=True
)


class CustomTemplateUploadForm(forms.ModelForm):
    """Form for uploading custom templates"""
    
    class Meta:
        model = CustomTemplate
        fields = [
            'name', 'description', 'html_file', 'css_file', 
            'preview_image', 'visibility', 'tags'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Modern Tech Resume'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe your template...'
            }),
            'html_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.html'
            }),
            'css_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.css'
            }),
            'preview_image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'visibility': forms.Select(attrs={'class': 'form-control'}),
            'tags': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'modern, tech, creative (comma-separated)'
            }),
        }
    
    def clean_html_file(self):
        """Validate HTML file"""
        html_file = self.cleaned_data.get('html_file')
        
        if html_file:
            # Check file size (max 2MB)
            if html_file.size > 2 * 1024 * 1024:
                raise forms.ValidationError("HTML file must be less than 2MB")
            
            # Read and validate HTML content
            content = html_file.read().decode('utf-8')
            html_file.seek(0)  # Reset file pointer
            
            # Check for required template variables
            required_vars = ['{{ resume.full_name }}', '{{ resume.email }}']
            missing_vars = [var for var in required_vars if var not in content]
            
            if missing_vars:
                raise forms.ValidationError(
                    f"Template must include: {', '.join(missing_vars)}"
                )
            
            # Check for potentially dangerous content
            dangerous_patterns = ['<script', 'javascript:', 'onerror=', 'onclick=']
            for pattern in dangerous_patterns:
                if pattern.lower() in content.lower():
                    raise forms.ValidationError(
                        f"Template contains potentially unsafe content: {pattern}"
                    )
        
        return html_file
    
    def clean_preview_image(self):
        """Validate preview image"""
        image = self.cleaned_data.get('preview_image')
        
        if image:
            # Check file size (max 5MB)
            if image.size > 5 * 1024 * 1024:
                raise forms.ValidationError("Image must be less than 5MB")
            
            # Validate image format
            from PIL import Image
            try:
                img = Image.open(image)
                img.verify()
            except Exception:
                raise forms.ValidationError("Invalid image file")
        
        return image


class TemplateRatingForm(forms.ModelForm):
    """Form for rating templates"""
    
    class Meta:
        model = TemplateRating
        fields = ['rating', 'review']
        widgets = {
            'rating': forms.RadioSelect(choices=[(i, f'{i} ★') for i in range(1, 6)]),
            'review': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Share your thoughts about this template...'
            })
        }