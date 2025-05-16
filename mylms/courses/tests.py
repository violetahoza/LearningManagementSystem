from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from .models import Course
from datetime import date, timedelta

class CourseModelTest(TestCase):
    """Test case for the Course model"""
    
    def setUp(self):
        self.teacher = User.objects.create_user(
            username='teacher',
            password='password123',
            email='teacher@example.com',
            role=User.TEACHER
        )
        
        # Create test courses
        self.active_course = Course.objects.create(
            title='Active Course',
            description='This is an active course',
            instructor=self.teacher,
            start_date=date.today() - timedelta(days=10),
            end_date=date.today() + timedelta(days=30)
        )
        
        self.past_course = Course.objects.create(
            title='Past Course',
            description='This is a past course',
            instructor=self.teacher,
            start_date=date.today() - timedelta(days=60),
            end_date=date.today() - timedelta(days=30)
        )
        
        self.future_course = Course.objects.create(
            title='Future Course',
            description='This is a future course',
            instructor=self.teacher,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=60)
        )
    
    def test_course_creation(self):
        """Test that courses are created correctly"""
        self.assertEqual(Course.objects.count(), 3)
        self.assertEqual(self.active_course.title, 'Active Course')
        self.assertEqual(self.active_course.instructor, self.teacher)
    
    def test_is_active_method(self):
        """Test that the is_active method returns correct values"""
        self.assertTrue(self.active_course.is_active())
        self.assertFalse(self.past_course.is_active())
        self.assertFalse(self.future_course.is_active())
    
    def test_string_representation(self):
        """Test string representation of Course model"""
        self.assertEqual(str(self.active_course), 'Active Course')

class CourseViewsTest(TestCase):
    """Test case for Course views"""
    
    def setUp(self):
        self.client = Client()
        
        # Create users
        self.admin = User.objects.create_user(
            username='admin',
            password='password123',
            email='admin@example.com',
            role=User.ADMIN
        )
        
        self.teacher = User.objects.create_user(
            username='teacher',
            password='password123',
            email='teacher@example.com',
            role=User.TEACHER
        )
        
        self.student = User.objects.create_user(
            username='student',
            password='password123',
            email='student@example.com',
            role=User.STUDENT
        )
        
        # Create course
        self.course = Course.objects.create(
            title='Test Course',
            description='This is a test course',
            instructor=self.teacher,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30)
        )
    
    def test_course_list_view(self):
        """Test course list view"""
        response = self.client.get(reverse('courses:course_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courses/course_list.html')
        self.assertContains(response, 'Test Course')
    
    def test_course_detail_view(self):
        """Test course detail view"""
        response = self.client.get(reverse('courses:course_detail', kwargs={'course_id': self.course.id}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courses/course_detail.html')
        self.assertContains(response, 'Test Course')
    
    def test_create_course_view_auth(self):
        """Test that only teachers and admins can access create course view"""
        # Unauthenticated user
        response = self.client.get(reverse('courses:create_course'))
        self.assertRedirects(response, f'/accounts/login/?next={reverse("courses:create_course")}')
        
        # Student
        self.client.login(username='student', password='password123')
        response = self.client.get(reverse('courses:create_course'))
        self.assertEqual(response.status_code, 403)  # Forbidden
        
        # Teacher
        self.client.login(username='teacher', password='password123')
        response = self.client.get(reverse('courses:create_course'))
        self.assertEqual(response.status_code, 200)
        
        # Admin
        self.client.login(username='admin', password='password123')
        response = self.client.get(reverse('courses:create_course'))
        self.assertEqual(response.status_code, 200)