# resumes/tests/test_views.py
from django.test import TestCase, Client
from django.urls import reverse

class ResumeBuilderTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user('test', 'test@test.com', 'pass')
        self.client.login(username='test', password='pass')
    
    def test_dashboard_access(self):
        response = self.client.get(reverse('resumes:dashboard'))
        self.assertEqual(response.status_code, 200)
    
    def test_create_resume_step1(self):
        response = self.client.post(reverse('resumes:resume_builder_step1_new'), {
            'title': 'My Resume',
            'full_name': 'Test User',
            'email': 'test@example.com'
        })
        self.assertEqual(Resume.objects.count(), 1)