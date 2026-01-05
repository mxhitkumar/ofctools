from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .views import *
from .models import *


class ExperienceInline(admin.TabularInline):
    model = Experience
    extra = 1
    fields = ('company', 'position', 'start_date', 'end_date', 'is_current', 'order')
    ordering = ['-start_date', 'order']


class EducationInline(admin.TabularInline):
    model = Education
    extra = 1
    fields = ('institution', 'degree', 'field_of_study', 'start_date', 'end_date', 'order')
    ordering = ['-start_date', 'order']


class SkillInline(admin.TabularInline):
    model = Skill
    extra = 3
    fields = ('name', 'category', 'proficiency', 'order')


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'full_name', 'user', 'template', 'ats_score_display', 
        'updated_at', 'is_active', 'actions_column'
    )
    list_filter = ('template', 'is_active', 'created_at', 'updated_at')
    search_fields = ('title', 'full_name', 'email', 'user__username')
    readonly_fields = ('id', 'created_at', 'updated_at', 'last_ats_check', 'preview_link')
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'id', 'user', 'title', 'template', 'is_active'
            )
        }),
        ('Personal Details', {
            'fields': (
                'full_name', 'email', 'phone', 'location',
                'linkedin_url', 'portfolio_url', 'github_url'
            )
        }),
        ('Professional Summary', {
            'fields': ('summary',)
        }),
        ('ATS Information', {
            'fields': ('target_job_title', 'ats_score', 'last_ats_check')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'preview_link'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [ExperienceInline, EducationInline, SkillInline]
    
    def ats_score_display(self, obj):
        if obj.ats_score >= 80:
            color = 'green'
        elif obj.ats_score >= 60:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}/100</span>',
            color, obj.ats_score
        )
    ats_score_display.short_description = 'ATS Score'
    
    def preview_link(self, obj):
        if obj.pk:
            url = reverse('resumes:resume_preview', args=[obj.pk])
            return format_html('<a href="{}" target="_blank">Preview Resume</a>', url)
        return '-'
    preview_link.short_description = 'Preview'
    
    def actions_column(self, obj):
        preview_url = reverse('resumes:resume_preview', args=[obj.pk])
        ats_url = reverse('resumes:ats_analyze', args=[obj.pk])
        pdf_url = reverse('resumes:export_pdf', args=[obj.pk])
        
        return format_html(
            '<a class="button" href="{}" target="_blank">Preview</a> '
            '<a class="button" href="{}">ATS</a> '
            '<a class="button" href="{}">PDF</a>',
            preview_url, ats_url, pdf_url
        )
    actions_column.short_description = 'Actions'


@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    list_display = ('position', 'company', 'resume', 'start_date', 'end_date', 'is_current')
    list_filter = ('is_current', 'start_date')
    search_fields = ('company', 'position', 'resume__full_name')
    date_hierarchy = 'start_date'


@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = ('degree', 'field_of_study', 'institution', 'resume', 'start_date', 'end_date', 'gpa')
    list_filter = ('degree', 'start_date')
    search_fields = ('institution', 'field_of_study', 'resume__full_name')


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'proficiency', 'resume')
    list_filter = ('category', 'proficiency')
    search_fields = ('name', 'resume__full_name')


@admin.register(Certification)
class CertificationAdmin(admin.ModelAdmin):
    list_display = ('name', 'issuing_organization', 'resume', 'issue_date', 'expiry_date')
    list_filter = ('issue_date', 'issuing_organization')
    search_fields = ('name', 'issuing_organization', 'resume__full_name')
    date_hierarchy = 'issue_date'


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'resume', 'technologies_list', 'start_date')
    list_filter = ('start_date',)
    search_fields = ('title', 'technologies', 'resume__full_name')
    
    def technologies_list(self, obj):
        techs = obj.technologies.split(',')[:3]
        return ', '.join([t.strip() for t in techs])
    technologies_list.short_description = 'Technologies'


@admin.register(ATSAnalysis)
class ATSAnalysisAdmin(admin.ModelAdmin):
    list_display = ('resume', 'score_display', 'created_at', 'view_details')
    list_filter = ('created_at', 'has_contact_info', 'has_clear_sections')
    search_fields = ('resume__full_name', 'resume__title')
    readonly_fields = (
        'resume', 'job_description', 'score', 'matched_keywords', 
        'missing_keywords', 'keyword_density', 'suggestions',
        'has_contact_info', 'has_clear_sections', 'has_measurable_achievements',
        'readability_score', 'created_at'
    )
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Analysis Info', {
            'fields': ('resume', 'created_at', 'score')
        }),
        ('Job Description', {
            'fields': ('job_description',)
        }),
        ('Keyword Analysis', {
            'fields': ('matched_keywords', 'missing_keywords', 'keyword_density')
        }),
        ('Format Checks', {
            'fields': (
                'has_contact_info', 'has_clear_sections', 
                'has_measurable_achievements', 'readability_score'
            )
        }),
        ('Suggestions', {
            'fields': ('suggestions',)
        }),
    )
    
    def score_display(self, obj):
        if obj.score >= 80:
            color = 'green'
            icon = '✓'
        elif obj.score >= 60:
            color = 'orange'
            icon = '!'
        else:
            color = 'red'
            icon = '✗'
        return format_html(
            '<span style="color: {}; font-weight: bold; font-size: 14px;">{} {}/100</span>',
            color, icon, obj.score
        )
    score_display.short_description = 'Score'
    
    def view_details(self, obj):
        url = reverse('resumes:ats_results', args=[obj.pk])
        return format_html('<a href="{}" target="_blank">View Full Report</a>', url)
    view_details.short_description = 'Report'


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'status', 'published_at', 'views', 'view_on_site')
    list_filter = ('status', 'published_at', 'created_at')
    search_fields = ('title', 'content', 'excerpt')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at', 'views')
    date_hierarchy = 'published_at'
    
    fieldsets = (
        ('Content', {
            'fields': ('title', 'slug', 'author', 'excerpt', 'content')
        }),
        ('Media', {
            'fields': ('featured_image',)
        }),
        ('Publishing', {
            'fields': ('status', 'published_at')
        }),
        ('Statistics', {
            'fields': ('views', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def view_on_site(self, obj):
        if obj.status == 'published':
            url = reverse('resumes:blog_detail', args=[obj.slug])
            return format_html('<a href="{}" target="_blank">View Post</a>', url)
        return '-'
    view_on_site.short_description = 'View'
    
    def save_model(self, request, obj, form, change):
        if not obj.author_id:
            obj.author = request.user
        if obj.status == 'published' and not obj.published_at:
            from django.utils import timezone
            obj.published_at = timezone.now()
        super().save_model(request, obj, form, change)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_premium', 'subscription_end_date', 'created_at')
    list_filter = ('is_premium', 'email_notifications')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('User', {
            'fields': ('user', 'bio', 'avatar')
        }),
        ('Subscription', {
            'fields': ('is_premium', 'subscription_end_date')
        }),
        ('Preferences', {
            'fields': ('default_template', 'email_notifications')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# Customize Admin Site
admin.site.site_header = 'Resume Builder Admin'
admin.site.site_title = 'Resume Builder'
admin.site.index_title = 'Dashboard'



@admin.register(CustomTemplate)
class CustomTemplateAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'creator', 'status', 'visibility', 
        'usage_count', 'rating', 'created_at'
    )
    list_filter = ('status', 'visibility', 'created_at')
    search_fields = ('name', 'description', 'creator__username')
    readonly_fields = ('usage_count', 'rating', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Template Info', {
            'fields': ('name', 'slug', 'description', 'creator')
        }),
        ('Files', {
            'fields': ('html_file', 'css_file', 'preview_image')
        }),
        ('Settings', {
            'fields': ('visibility', 'status', 'tags')
        }),
        ('Configuration', {
            'fields': ('template_config',),
            'classes': ('collapse',)
        }),
        ('Review', {
            'fields': ('reviewed_by', 'review_notes')
        }),
        ('Stats', {
            'fields': ('usage_count', 'rating', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_templates', 'reject_templates']
    
    def approve_templates(self, request, queryset):
        queryset.update(status='approved', reviewed_by=request.user)
        self.message_user(request, f'{queryset.count()} template(s) approved.')
    approve_templates.short_description = 'Approve selected templates'
    
    def reject_templates(self, request, queryset):
        queryset.update(status='rejected', reviewed_by=request.user)
        self.message_user(request, f'{queryset.count()} template(s) rejected.')
    reject_templates.short_description = 'Reject selected templates'


@admin.register(TemplateRating)
class TemplateRatingAdmin(admin.ModelAdmin):
    list_display = ('template', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('template__name', 'user__username', 'review')
    
    
# In admin.py
@admin.action(description='Export selected resumes as PDF')
def export_resumes_as_pdf(modeladmin, request, queryset):
    import zipfile
    from io import BytesIO
    
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        for resume in queryset:
            pdf = generate_resume_pdf(resume)
            filename = f"{resume.full_name}_Resume.pdf"
            zip_file.writestr(filename, pdf)
    
    response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="resumes.zip"'
    return response

class ResumeAdmin(admin.ModelAdmin):
    actions = [export_resumes_as_pdf]