from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from django.template.loader import render_to_string

from .models import Resume, Experience, Education, Skill, ATSAnalysis, BlogPost
from .forms import (
    ResumeBasicForm, ExperienceFormSet, EducationFormSet, 
    SkillFormSet, CertificationFormSet, ProjectFormSet,
    TemplateSelectionForm, ATSAnalysisForm
)
from .ats_analyzer import ATSAnalyzer
from .pdf_generator import generate_resume_pdf


# ============= Dashboard Views =============

@login_required
def dashboard(request):
    """User dashboard showing all resumes"""
    resumes = Resume.objects.filter(user=request.user, is_active=True)
    
    context = {
        'resumes': resumes,
        'total_resumes': resumes.count(),
        'recent_analyses': ATSAnalysis.objects.filter(
            resume__user=request.user
        ).order_by('-created_at')[:5]
    }
    return render(request, 'resumes/dashboard.html', context)


# ============= Multi-Step Resume Builder =============

@login_required
def resume_builder_step1(request, pk=None):
    """Step 1: Basic Information"""
    if pk:
        resume = get_object_or_404(Resume, pk=pk, user=request.user)
        form = ResumeBasicForm(request.POST or None, instance=resume)
    else:
        form = ResumeBasicForm(request.POST or None)
    
    if request.method == 'POST' and form.is_valid():
        resume = form.save(commit=False)
        if not pk:
            resume.user = request.user
        resume.save()
        messages.success(request, 'Basic information saved!')
        return redirect('resume_builder_step2', pk=resume.pk)
    
    context = {
        'form': form,
        'step': 1,
        'resume': resume if pk else None
    }
    return render(request, 'resumes/builder_step1.html', context)


@login_required
@transaction.atomic
def resume_builder_step2(request, pk):
    """Step 2: Work Experience (with formsets)"""
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    
    if request.method == 'POST':
        formset = ExperienceFormSet(request.POST, instance=resume)
        if formset.is_valid():
            formset.save()
            messages.success(request, 'Work experience saved!')
            return redirect('resume_builder_step3', pk=resume.pk)
    else:
        formset = ExperienceFormSet(instance=resume)
    
    context = {
        'formset': formset,
        'resume': resume,
        'step': 2
    }
    return render(request, 'resumes/builder_step2.html', context)


@login_required
@transaction.atomic
def resume_builder_step3(request, pk):
    """Step 3: Education"""
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    
    if request.method == 'POST':
        formset = EducationFormSet(request.POST, instance=resume)
        if formset.is_valid():
            formset.save()
            messages.success(request, 'Education saved!')
            return redirect('resume_builder_step4', pk=resume.pk)
    else:
        formset = EducationFormSet(instance=resume)
    
    context = {
        'formset': formset,
        'resume': resume,
        'step': 3
    }
    return render(request, 'resumes/builder_step3.html', context)


@login_required
@transaction.atomic
def resume_builder_step4(request, pk):
    """Step 4: Skills"""
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    
    if request.method == 'POST':
        skill_formset = SkillFormSet(request.POST, instance=resume, prefix='skills')
        cert_formset = CertificationFormSet(request.POST, instance=resume, prefix='certs')
        project_formset = ProjectFormSet(request.POST, instance=resume, prefix='projects')
        
        if all([skill_formset.is_valid(), cert_formset.is_valid(), project_formset.is_valid()]):
            skill_formset.save()
            cert_formset.save()
            project_formset.save()
            messages.success(request, 'Skills and additional sections saved!')
            return redirect('resume_builder_step5', pk=resume.pk)
    else:
        skill_formset = SkillFormSet(instance=resume, prefix='skills')
        cert_formset = CertificationFormSet(instance=resume, prefix='certs')
        project_formset = ProjectFormSet(instance=resume, prefix='projects')
    
    context = {
        'skill_formset': skill_formset,
        'cert_formset': cert_formset,
        'project_formset': project_formset,
        'resume': resume,
        'step': 4
    }
    return render(request, 'resumes/builder_step4.html', context)


@login_required
def resume_builder_step5(request, pk):
    """Step 5: Template Selection & Preview"""
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = TemplateSelectionForm(request.POST, instance=resume)
        if form.is_valid():
            form.save()
            messages.success(request, 'Resume completed successfully!')
            return redirect('resume_preview', pk=resume.pk)
    else:
        form = TemplateSelectionForm(instance=resume)
    
    # Get all template choices for preview
    templates = Resume.TEMPLATE_CHOICES
    
    context = {
        'form': form,
        'resume': resume,
        'templates': templates,
        'step': 5
    }
    return render(request, 'resumes/builder_step5.html', context)


# ============= Resume CRUD Views =============

@login_required
def resume_preview(request, pk):
    """Preview resume with selected template"""
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    
    # Get the template path based on selection
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


@login_required
def resume_delete(request, pk):
    """Delete resume (soft delete)"""
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    
    if request.method == 'POST':
        resume.is_active = False
        resume.save()
        messages.success(request, 'Resume deleted successfully.')
        return redirect('dashboard')
    
    return render(request, 'resumes/resume_confirm_delete.html', {'resume': resume})


@login_required
def resume_duplicate(request, pk):
    """Duplicate an existing resume"""
    original = get_object_or_404(Resume, pk=pk, user=request.user)
    
    # Create a copy
    resume_copy = Resume.objects.get(pk=original.pk)
    resume_copy.pk = None
    resume_copy.title = f"{original.title} (Copy)"
    resume_copy.save()
    
    # Copy related objects
    for exp in original.experiences.all():
        exp.pk = None
        exp.resume = resume_copy
        exp.save()
    
    for edu in original.educations.all():
        edu.pk = None
        edu.resume = resume_copy
        edu.save()
    
    for skill in original.skills.all():
        skill.pk = None
        skill.resume = resume_copy
        skill.save()
    
    messages.success(request, 'Resume duplicated successfully!')
    return redirect('resume_builder_step1', pk=resume_copy.pk)


# ============= ATS Analysis Views =============

@login_required
def ats_analyze(request, pk):
    """ATS Analysis tool"""
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = ATSAnalysisForm(request.POST)
        if form.is_valid():
            job_description = form.cleaned_data['job_description']
            
            # Run ATS analysis
            analyzer = ATSAnalyzer(resume, job_description)
            analysis = analyzer.analyze()
            
            messages.success(request, f'ATS Score: {analysis.score}/100')
            return redirect('ats_results', pk=analysis.pk)
    else:
        form = ATSAnalysisForm()
    
    context = {
        'form': form,
        'resume': resume,
        'previous_analyses': ATSAnalysis.objects.filter(resume=resume).order_by('-created_at')[:5]
    }
    return render(request, 'resumes/ats_analyze.html', context)


@login_required
def ats_results(request, pk):
    """Display ATS analysis results"""
    analysis = get_object_or_404(ATSAnalysis, pk=pk, resume__user=request.user)
    
    context = {
        'analysis': analysis,
        'resume': analysis.resume
    }
    return render(request, 'resumes/ats_results.html', context)


# ============= PDF Export Views =============

@login_required
def export_pdf(request, pk):
    """Export resume as PDF"""
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    
    try:
        pdf = generate_resume_pdf(resume)
        
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{resume.full_name}_Resume.pdf"'
        return response
    
    except Exception as e:
        messages.error(request, f'Error generating PDF: {str(e)}')
        return redirect('resume_preview', pk=pk)


# ============= AJAX Views for Dynamic Forms =============

@login_required
def ajax_change_template(request, pk):
    """AJAX view to change template and return preview HTML"""
    if request.method == 'POST':
        resume = get_object_or_404(Resume, pk=pk, user=request.user)
        template = request.POST.get('template')
        
        if template in dict(Resume.TEMPLATE_CHOICES):
            resume.template = template
            resume.save()
            
            # Render the new template
            template_name = f'resumes/templates/{template}.html'
            context = {
                'resume': resume,
                'experiences': resume.experiences.all(),
                'educations': resume.educations.all(),
                'skills': resume.skills.all(),
                'certifications': resume.certifications.all(),
                'projects': resume.projects.all(),
            }
            
            html = render_to_string(template_name, context, request)
            return JsonResponse({'success': True, 'html': html})
    
    return JsonResponse({'success': False})


# ============= Blog Views =============

class BlogListView(ListView):
    """List all published blog posts"""
    model = BlogPost
    template_name = 'blog/list.html'
    context_object_name = 'posts'
    paginate_by = 10
    
    def get_queryset(self):
        return BlogPost.objects.filter(status='published').order_by('-published_at')


class BlogDetailView(DetailView):
    """Display a single blog post"""
    model = BlogPost
    template_name = 'blog/detail.html'
    context_object_name = 'post'
    slug_field = 'slug'
    
    def get_queryset(self):
        return BlogPost.objects.filter(status='published')
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # Increment view count
        obj.views += 1
        obj.save(update_fields=['views'])
        return obj


# ============= Public Landing Page =============

def landing_page(request):
    """Public landing page"""
    context = {
        'recent_posts': BlogPost.objects.filter(status='published')[:3]
    }
    return render(request, 'landing.html', context)

from django.views.decorators.clickjacking import xframe_options_exempt

@xframe_options_exempt
def template_preview(request, slug):
    """
    Preview template with sample data (for iframe)
    """
    template = get_object_or_404(CustomTemplate, slug=slug, status='approved')
    
    # Create sample resume data
    from django.contrib.auth.models import User
    sample_user = User.objects.first()
    
    # Get a sample resume or create dummy data
    sample_resume = Resume.objects.filter(user=sample_user).first()
    
    if not sample_resume:
        # Create temporary sample data
        class SampleResume:
            full_name = "John Doe"
            email = "john.doe@example.com"
            phone = "+1 (555) 123-4567"
            location = "San Francisco, CA"
            summary = "Experienced professional with 5+ years in the industry..."
            linkedin_url = "https://linkedin.com/in/johndoe"
            portfolio_url = "https://johndoe.com"
            github_url = "https://github.com/johndoe"
        
        sample_resume = SampleResume()
    
    try:
        html_content = SecureTemplateRenderer.render_custom_template(
            template,
            sample_resume
        )
        return HttpResponse(html_content)
    except Exception as e:
        return HttpResponse(f"<h3>Error loading preview: {str(e)}</h3>")