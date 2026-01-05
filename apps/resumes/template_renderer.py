"""
Secure custom template rendering system
"""

from django.template import Template, Context
from django.template.exceptions import TemplateSyntaxError
from django.utils.html import escape
import re


class SecureTemplateRenderer:
    """Safely render user-uploaded templates"""
    
    # Allowed Django template tags
    ALLOWED_TAGS = [
        'if', 'endif', 'for', 'endfor', 'with', 'endwith',
        'block', 'endblock', 'load', 'static'
    ]
    
    # Blocked dangerous patterns
    DANGEROUS_PATTERNS = [
        r'<script[^>]*>',
        r'javascript:',
        r'onerror\s*=',
        r'onclick\s*=',
        r'onload\s*=',
        r'eval\(',
        r'exec\(',
        r'__import__',
        r'{% include',
        r'{% ssi',
    ]
    
    @classmethod
    def validate_template(cls, template_content):
        """
        Validate template for security issues
        Returns: (is_valid, error_message)
        """
        
        # Check for dangerous patterns
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, template_content, re.IGNORECASE):
                return False, f"Template contains unsafe content: {pattern}"
        
        # Try to compile template
        try:
            Template(template_content)
        except TemplateSyntaxError as e:
            return False, f"Template syntax error: {str(e)}"
        
        return True, None
    
    @classmethod
    def render_custom_template(cls, template, resume):
        """
        Safely render a custom template with resume data
        
        Args:
            template: CustomTemplate instance
            resume: Resume instance
        
        Returns:
            Rendered HTML string
        """
        
        # Read template file
        try:
            with template.html_file.open('r') as f:
                template_content = f.read()
        except Exception as e:
            raise Exception(f"Error reading template file: {str(e)}")
        
        # Validate template
        is_valid, error_msg = cls.validate_template(template_content)
        if not is_valid:
            raise Exception(error_msg)
        
        # Read CSS if provided
        css_content = ""
        if template.css_file:
            try:
                with template.css_file.open('r') as f:
                    css_content = f.read()
            except Exception:
                pass
        
        # Inject CSS into template if not already present
        if css_content and '<style>' not in template_content:
            style_tag = f'<style>{css_content}</style>'
            if '</head>' in template_content:
                template_content = template_content.replace('</head>', f'{style_tag}</head>')
            else:
                template_content = style_tag + template_content
        
        # Prepare context data
        context_data = cls._prepare_context(resume)
        
        # Render template
        try:
            django_template = Template(template_content)
            context = Context(context_data)
            rendered_html = django_template.render(context)
        except Exception as e:
            raise Exception(f"Error rendering template: {str(e)}")
        
        return rendered_html
    
    @classmethod
    def _prepare_context(cls, resume):
        """Prepare context data for template rendering"""
        
        return {
            'resume': resume,
            'experiences': resume.experiences.all().order_by('-start_date'),
            'educations': resume.educations.all().order_by('-start_date'),
            'skills': resume.skills.all(),
            'certifications': resume.certifications.all().order_by('-issue_date'),
            'projects': resume.projects.all().order_by('-start_date'),
        }


# ============================================
# resumes/views.py (update resume_preview view)
# ============================================

from .template_renderer import SecureTemplateRenderer

@login_required
def resume_preview(request, pk):
    """Preview resume with selected template (including custom)"""
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    
    # Check if using custom template
    if resume.template == 'custom' and resume.custom_template:
        try:
            # Render custom template securely
            html_content = SecureTemplateRenderer.render_custom_template(
                resume.custom_template,
                resume
            )
            
            # Return rendered custom template
            from django.http import HttpResponse
            return HttpResponse(html_content)
        
        except Exception as e:
            messages.error(request, f'Error rendering custom template: {str(e)}')
            # Fall back to default template
            resume.template = 'professional'
            resume.save()
    
    # Use built-in template
    template_name = f'resumes/templates/{resume.template}.html'
    
    context = {
        'resume': resume,
        'experiences': resume.experiences.all(),
        'educations': resume.educations.all(),
        'skills': resume.skills.all(),
        'certifications': resume.certifications.all(),
        'projects': resume.projects.all(),
    }
    
    return render(request, template_name, context)