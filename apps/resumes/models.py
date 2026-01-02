from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
import uuid

class Resume(models.Model):
    """Core Resume model - one user can have multiple resumes"""
    TEMPLATE_CHOICES = [
        ('professional', 'Professional'),
        ('creative', 'Creative'),
        ('modern', 'Modern'),
        ('minimal', 'Minimal'),
        ('executive', 'Executive'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resumes')
    title = models.CharField(max_length=200, help_text="Internal name for this resume")
    template = models.CharField(max_length=50, choices=TEMPLATE_CHOICES, default='professional')
    
    # Personal Information
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=200, blank=True)
    linkedin_url = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    
    # Professional Summary
    summary = models.TextField(blank=True, help_text="Professional summary or objective")
    
    # ATS Optimization
    target_job_title = models.CharField(max_length=200, blank=True)
    ats_score = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    last_ats_check = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', '-updated_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.full_name}"
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('resume_detail', kwargs={'pk': self.pk})


class Experience(models.Model):
    """Work Experience entries"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='experiences')
    
    company = models.CharField(max_length=200)
    position = models.CharField(max_length=200)
    location = models.CharField(max_length=200, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True, help_text="Leave blank if current")
    is_current = models.BooleanField(default=False)
    description = models.TextField(help_text="Job responsibilities and achievements")
    
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['resume', '-start_date', 'order']
        indexes = [
            models.Index(fields=['resume', '-start_date']),
        ]
    
    def __str__(self):
        return f"{self.position} at {self.company}"
    
    @property
    def duration(self):
        """Calculate duration of employment"""
        from datetime import date
        end = self.end_date or date.today()
        delta = end - self.start_date
        years = delta.days // 365
        months = (delta.days % 365) // 30
        
        if years > 0:
            return f"{years} year{'s' if years > 1 else ''}, {months} month{'s' if months != 1 else ''}"
        return f"{months} month{'s' if months != 1 else ''}"


class Education(models.Model):
    """Education entries"""
    DEGREE_CHOICES = [
        ('high_school', 'High School Diploma'),
        ('associate', 'Associate Degree'),
        ('bachelor', 'Bachelor\'s Degree'),
        ('master', 'Master\'s Degree'),
        ('phd', 'Ph.D.'),
        ('certificate', 'Certificate'),
        ('bootcamp', 'Bootcamp'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='educations')
    
    institution = models.CharField(max_length=200)
    degree = models.CharField(max_length=50, choices=DEGREE_CHOICES)
    field_of_study = models.CharField(max_length=200)
    location = models.CharField(max_length=200, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    gpa = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    description = models.TextField(blank=True, help_text="Honors, relevant coursework, etc.")
    
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['resume', '-start_date', 'order']
        verbose_name_plural = "Education"
    
    def __str__(self):
        return f"{self.degree} in {self.field_of_study} - {self.institution}"


class Skill(models.Model):
    """Skills with proficiency levels"""
    PROFICIENCY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]
    
    CATEGORY_CHOICES = [
        ('technical', 'Technical'),
        ('language', 'Language'),
        ('soft', 'Soft Skills'),
        ('tools', 'Tools & Software'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='skills')
    
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='technical')
    proficiency = models.CharField(max_length=20, choices=PROFICIENCY_CHOICES, default='intermediate')
    
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['resume', 'category', 'order']
        unique_together = ['resume', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.proficiency})"


class Certification(models.Model):
    """Professional certifications"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='certifications')
    
    name = models.CharField(max_length=200)
    issuing_organization = models.CharField(max_length=200)
    issue_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    credential_id = models.CharField(max_length=200, blank=True)
    credential_url = models.URLField(blank=True)
    
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['resume', '-issue_date', 'order']
    
    def __str__(self):
        return f"{self.name} - {self.issuing_organization}"


class Project(models.Model):
    """Portfolio projects"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='projects')
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    technologies = models.CharField(max_length=500, help_text="Comma-separated list")
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    project_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['resume', '-start_date', 'order']
    
    def __str__(self):
        return self.title


class ATSAnalysis(models.Model):
    """Store ATS analysis results"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='ats_analyses')
    
    job_description = models.TextField()
    score = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Analysis Results
    matched_keywords = models.JSONField(default=list)
    missing_keywords = models.JSONField(default=list)
    keyword_density = models.JSONField(default=dict)
    suggestions = models.JSONField(default=list)
    
    # Formatting checks
    has_contact_info = models.BooleanField(default=True)
    has_clear_sections = models.BooleanField(default=True)
    has_measurable_achievements = models.BooleanField(default=False)
    readability_score = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "ATS Analyses"
    
    def __str__(self):
        return f"ATS Analysis for {self.resume.title} - Score: {self.score}"


class BlogPost(models.Model):
    """Resume tips and career advice blog"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_posts')
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    excerpt = models.TextField(max_length=500)
    content = models.TextField()
    
    featured_image = models.ImageField(upload_to='blog/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    views = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-published_at']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title


class UserProfile(models.Model):
    """Extended user profile"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    
    # Subscription info (for future premium features)
    is_premium = models.BooleanField(default=False)
    subscription_end_date = models.DateField(null=True, blank=True)
    
    # Preferences
    default_template = models.CharField(max_length=50, default='professional')
    email_notifications = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Profile for {self.user.username}"