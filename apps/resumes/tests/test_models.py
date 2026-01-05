# resumes/tests/test_models.py
from django.test import TestCase
from django.contrib.auth.models import User
from resumes.models import Resume, Experience

class ResumeModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@test.com', 'pass')
        self.resume = Resume.objects.create(
            user=self.user,
            title='Test Resume',
            full_name='John Doe',
            email='john@example.com'
        )
    
    def test_resume_creation(self):
        self.assertEqual(self.resume.full_name, 'John Doe')
        self.assertEqual(self.resume.user, self.user)
    
    def test_experience_relationship(self):
        exp = Experience.objects.create(
            resume=self.resume,
            company='Test Corp',
            position='Developer',
            start_date='2020-01-01'
        )
        self.assertEqual(self.resume.experiences.count(), 1)