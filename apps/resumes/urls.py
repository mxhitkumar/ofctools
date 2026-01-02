from django.urls import path
from . import views

app_name = 'resumes'

urlpatterns = [
    # Landing & Dashboard
    path('', views.landing_page, name='landing'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Multi-Step Resume Builder
    path('builder/step1/', views.resume_builder_step1, name='resume_builder_step1_new'),
    path('builder/step1/<uuid:pk>/', views.resume_builder_step1, name='resume_builder_step1'),
    path('builder/step2/<uuid:pk>/', views.resume_builder_step2, name='resume_builder_step2'),
    path('builder/step3/<uuid:pk>/', views.resume_builder_step3, name='resume_builder_step3'),
    path('builder/step4/<uuid:pk>/', views.resume_builder_step4, name='resume_builder_step4'),
    path('builder/step5/<uuid:pk>/', views.resume_builder_step5, name='resume_builder_step5'),
    
    # Resume Management
    path('resume/<uuid:pk>/preview/', views.resume_preview, name='resume_preview'),
    path('resume/<uuid:pk>/delete/', views.resume_delete, name='resume_delete'),
    path('resume/<uuid:pk>/duplicate/', views.resume_duplicate, name='resume_duplicate'),
    path('resume/<uuid:pk>/export/pdf/', views.export_pdf, name='export_pdf'),
    
    # ATS Analysis
    path('resume/<uuid:pk>/ats-analyze/', views.ats_analyze, name='ats_analyze'),
    path('ats/results/<uuid:pk>/', views.ats_results, name='ats_results'),
    
    # AJAX
    path('ajax/change-template/<uuid:pk>/', views.ajax_change_template, name='ajax_change_template'),
    
    # Blog
    path('blog/', views.BlogListView.as_view(), name='blog_list'),
    path('blog/<slug:slug>/', views.BlogDetailView.as_view(), name='blog_detail'),
]