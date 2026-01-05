from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from django.template.loader import render_to_string

from .template_renderer import SecureTemplateRenderer

from .models import *
from .forms import *
from .ats_analyzer import ATSAnalyzer
from .pdf_generator import generate_resume_pdf


# ============= Dashboard Views =============

# @login_required
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

# @login_required
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


# @login_required
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


# @login_required
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


# @login_required
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


# @login_required
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

# @login_required
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


# @login_required
def resume_delete(request, pk):
    """Delete resume (soft delete)"""
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    
    if request.method == 'POST':
        resume.is_active = False
        resume.save()
        messages.success(request, 'Resume deleted successfully.')
        return redirect('dashboard')
    
    return render(request, 'resumes/resume_confirm_delete.html', {'resume': resume})


# @login_required
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

# @login_required
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


# @login_required
def ats_results(request, pk):
    """Display ATS analysis results"""
    analysis = get_object_or_404(ATSAnalysis, pk=pk, resume__user=request.user)
    
    context = {
        'analysis': analysis,
        'resume': analysis.resume
    }
    return render(request, 'resumes/ats_results.html', context)


# ============= PDF Export Views =============

# @login_required
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

# @login_required
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
    
    
    
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Avg
from .models import CustomTemplate, TemplateRating
from .forms import CustomTemplateUploadForm, TemplateRatingForm

# @login_required
def template_marketplace(request):
    """Browse and search custom templates"""
    
    # Get filter parameters
    search_query = request.GET.get('q', '')
    visibility = request.GET.get('visibility', 'all')
    sort_by = request.GET.get('sort', 'popular')
    
    # Base queryset - approved templates
    templates = CustomTemplate.objects.filter(status='approved')
    
    # Filter by visibility
    if visibility == 'public':
        templates = templates.filter(visibility='public')
    elif visibility == 'premium':
        templates = templates.filter(visibility='premium')
    
    # Search
    if search_query:
        templates = templates.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(tags__icontains=search_query)
        )
    
    # Sorting
    if sort_by == 'popular':
        templates = templates.order_by('-usage_count')
    elif sort_by == 'rating':
        templates = templates.annotate(avg_rating=Avg('ratings__rating')).order_by('-avg_rating')
    elif sort_by == 'newest':
        templates = templates.order_by('-created_at')
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(templates, 12)
    page_number = request.GET.get('page')
    templates_page = paginator.get_page(page_number)
    
    context = {
        'templates': templates_page,
        'search_query': search_query,
        'visibility': visibility,
        'sort_by': sort_by,
    }
    
    return render(request, 'resumes/template_marketplace.html', context)


# @login_required
def upload_custom_template(request):
    """Upload a new custom template"""
    
    if request.method == 'POST':
        form = CustomTemplateUploadForm(request.POST, request.FILES)
        
        if form.is_valid():
            template = form.save(commit=False)
            template.creator = request.user
            template.status = 'draft'  # Start as draft
            
            # Parse template to extract configuration
            template.template_config = parse_template_config(
                request.FILES['html_file']
            )
            
            template.save()
            
            messages.success(
                request,
                'Template uploaded successfully! It will be reviewed before going live.'
            )
            return redirect('resumes:my_templates')
        
    else:
        form = CustomTemplateUploadForm()
    
    context = {
        'form': form,
        'template_guide': get_template_guide(),
    }
    
    return render(request, 'resumes/upload_template.html', context)


# @login_required
def my_templates(request):
    """View user's uploaded templates"""
    
    templates = CustomTemplate.objects.filter(
        creator=request.user
    ).order_by('-created_at')
    
    context = {
        'templates': templates,
    }
    
    return render(request, 'resumes/my_templates.html', context)


# @login_required
def template_detail(request, slug):
    """View template details"""
    
    template = get_object_or_404(CustomTemplate, slug=slug, status='approved')
    
    # Check if user can view this template
    if template.visibility == 'private' and template.creator != request.user:
        messages.error(request, 'This template is private.')
        return redirect('resumes:template_marketplace')
    
    if template.visibility == 'premium':
        if not request.user.subscription.is_premium():
            messages.warning(request, 'This template requires a premium subscription.')
            return redirect('subscription_plans')
    
    # Get ratings
    ratings = template.ratings.all()
    user_rating = ratings.filter(user=request.user).first()
    
    # Handle rating form
    if request.method == 'POST':
        rating_form = TemplateRatingForm(request.POST)
        if rating_form.is_valid():
            rating = rating_form.save(commit=False)
            rating.template = template
            rating.user = request.user
            rating.save()
            
            # Update template average rating
            avg_rating = template.ratings.aggregate(Avg('rating'))['rating__avg']
            template.rating = avg_rating or 0
            template.save()
            
            messages.success(request, 'Thank you for your rating!')
            return redirect('resumes:template_detail', slug=slug)
    else:
        rating_form = TemplateRatingForm(instance=user_rating)
    
    context = {
        'template': template,
        'ratings': ratings[:10],
        'user_rating': user_rating,
        'rating_form': rating_form,
        'can_use': can_use_template(request.user, template),
    }
    
    return render(request, 'resumes/template_detail.html', context)


# @login_required
def use_custom_template(request, slug):
    """Use a custom template for a resume"""
    
    template = get_object_or_404(CustomTemplate, slug=slug, status='approved')
    
    # Check permissions
    if not can_use_template(request.user, template):
        messages.error(request, 'You cannot use this template.')
        return redirect('resumes:template_detail', slug=slug)
    
    # Get or create resume
    resume_id = request.GET.get('resume_id')
    if resume_id:
        resume = get_object_or_404(Resume, pk=resume_id, user=request.user)
        resume.custom_template = template
        resume.template = 'custom'
        resume.save()
        
        # Increment usage count
        template.increment_usage()
        
        messages.success(request, f'Now using template: {template.name}')
        return redirect('resumes:resume_preview', pk=resume.pk)
    
    return redirect('resumes:dashboard')


# @login_required
def delete_custom_template(request, slug):
    """Delete a custom template"""
    
    template = get_object_or_404(CustomTemplate, slug=slug, creator=request.user)
    
    if request.method == 'POST':
        # Check if any resumes are using this template
        resumes_using = Resume.objects.filter(custom_template=template).count()
        
        if resumes_using > 0:
            messages.warning(
                request,
                f'Cannot delete. {resumes_using} resume(s) are using this template.'
            )
        else:
            template.delete()
            messages.success(request, 'Template deleted successfully.')
        
        return redirect('resumes:my_templates')
    
    return render(request, 'resumes/template_confirm_delete.html', {'template': template})


# ============================================
# Helper Functions
# ============================================

def parse_template_config(html_file):
    """Parse HTML template to extract configuration"""
    
    content = html_file.read().decode('utf-8')
    html_file.seek(0)
    
    config = {
        'has_experience': '{% for exp in experiences %}' in content,
        'has_education': '{% for edu in educations %}' in content,
        'has_skills': '{% for skill in skills %}' in content,
        'has_certifications': '{% for cert in certifications %}' in content,
        'has_projects': '{% for project in projects %}' in content,
        'has_summary': '{{ resume.summary }}' in content,
    }
    
    return config


def can_use_template(user, template):
    """Check if user can use a template"""
    
    # Creator can always use their own templates
    if template.creator == user:
        return True
    
    # Check visibility
    if template.visibility == 'private':
        return False
    
    if template.visibility == 'premium':
        return user.subscription.is_premium()
    
    # Public templates
    return True


def get_template_guide():
    """Get template creation guide"""
    
    return {
        'required_variables': [
            '{{ resume.full_name }}',
            '{{ resume.email }}',
        ],
        'optional_variables': [
            '{{ resume.phone }}',
            '{{ resume.location }}',
            '{{ resume.summary }}',
            '{{ resume.linkedin_url }}',
            '{{ resume.portfolio_url }}',
            '{{ resume.github_url }}',
        ],
        'loops': [
            'experiences',
            'educations',
            'skills',
            'certifications',
            'projects',
        ],
        'example_code': '''
{% load static %}
<!DOCTYPE html>
<html>
<head>
    <title>{{ resume.full_name }} - Resume</title>
    <style>
        /* Your CSS here */
    </style>
</head>
<body>
    <h1>{{ resume.full_name }}</h1>
    <p>{{ resume.email }}</p>
    
    {% if resume.summary %}
    <section>
        <h2>Summary</h2>
        <p>{{ resume.summary }}</p>
    </section>
    {% endif %}
    
    {% if experiences %}
    <section>
        <h2>Experience</h2>
        {% for exp in experiences %}
        <div>
            <h3>{{ exp.position }}</h3>
            <p>{{ exp.company }}</p>
            <p>{{ exp.description }}</p>
        </div>
        {% endfor %}
    </section>
    {% endif %}
</body>
</html>
        '''
    }
    
    
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from .stripe_service import StripeService

# @login_required
def subscription_plans(request):
    """Display subscription plans"""
    current_subscription = request.user.subscription
    
    plans = [
        {
            'name': 'Free',
            'price': 0,
            'features': [
                '3 resumes',
                'Basic templates',
                'PDF export',
                'ATS scoring',
            ]
        },
        {
            'name': 'Basic',
            'price': 9.99,
            'plan_id': 'basic',
            'features': [
                '10 resumes',
                'All templates',
                'PDF export',
                'ATS scoring',
                '10 AI suggestions/month',
                'Priority support',
            ]
        },
        {
            'name': 'Pro',
            'price': 19.99,
            'plan_id': 'pro',
            'popular': True,
            'features': [
                'Unlimited resumes',
                'All templates',
                'PDF & DOCX export',
                'Advanced ATS scoring',
                '50 AI suggestions/month',
                'Cover letter generator',
                'LinkedIn import',
                'Priority support',
            ]
        },
        {
            'name': 'Enterprise',
            'price': 49.99,
            'plan_id': 'enterprise',
            'features': [
                'Everything in Pro',
                '200 AI suggestions/month',
                'Team collaboration',
                'Custom branding',
                'API access',
                'Dedicated support',
            ]
        },
    ]
    
    return render(request, 'subscription/plans.html', {
        'plans': plans,
        'current_subscription': current_subscription
    })

# @login_required
def create_checkout_session(request, plan):
    """Create Stripe checkout session"""
    try:
        session = StripeService.create_checkout_session(request.user, plan)
        return JsonResponse({'checkout_url': session.url})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

# @login_required
def subscription_success(request):
    """Handle successful subscription"""
    session_id = request.GET.get('session_id')
    
    # Verify session
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        if session.payment_status == 'paid':
            messages.success(request, 'Welcome to premium! Your subscription is now active.')
        else:
            messages.warning(request, 'Payment is being processed.')
    
    except Exception as e:
        messages.error(request, 'Error verifying payment.')
    
    return redirect('dashboard')

# @login_required
def manage_subscription(request):
    """Redirect to Stripe customer portal"""
    try:
        portal_session = StripeService.create_billing_portal_session(request.user)
        return redirect(portal_session.url)
    
    except Exception as e:
        messages.error(request, str(e))
        return redirect('dashboard')

# @login_required
def cancel_subscription(request):
    """Cancel subscription"""
    if request.method == 'POST':
        try:
            StripeService.cancel_subscription(request.user)
            messages.success(
                request,
                'Your subscription will be cancelled at the end of the billing period.'
            )
        except Exception as e:
            messages.error(request, str(e))
    
    return redirect('dashboard')

@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhooks"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = StripeService.handle_webhook(payload, sig_header)
        return HttpResponse(status=200)
    
    except Exception as e:
        return HttpResponse(status=400)


# ============================================
# Feature-gated decorators
# ============================================

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def premium_required(view_func):
    """Decorator to require premium subscription"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        subscription = request.user.subscription
        if not subscription.is_premium():
            messages.warning(
                request,
                'This feature requires a premium subscription.'
            )
            return redirect('subscription_plans')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper

def can_create_resume(view_func):
    """Check if user can create more resumes"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        subscription = request.user.subscription
        
        if not subscription.can_create_resume():
            messages.warning(
                request,
                f'You\'ve reached your limit of {subscription.max_resumes} resumes. '
                'Upgrade to create more!'
            )
            return redirect('subscription_plans')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


# Usage example:
# @login_required
@can_create_resume
def resume_builder_step1(request):
    # Your view logic
    pass

# @login_required
@premium_required
def ai_suggest_content(request):
    # AI feature only for premium users
    pass


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create user profile
            UserProfile.objects.create(user=user)
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


@login_required
def profile_edit(request):
    profile = request.user.profile
    if request.method == 'POST':
        # Handle profile updates
        pass
    return render(request, 'profile/edit.html', {'profile': profile})