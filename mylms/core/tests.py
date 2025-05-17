from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
import json

from accounts.models import User
from courses.models import Course
from lessons.models import Lesson
from enrollments.models import Enrollment
from quizzes.models import Quiz, Question, Answer
from progress.models import Progress
from certificates.models import Certificate

class LMSTestCase(TestCase):
    """Base test case with common setup for all LMS test cases"""
    
    def setUp(self):
        """Set up common test data for all tests"""
        # Create users with different roles
        self.admin = User.objects.create_user(
            username='admin_user',
            email='admin@example.com',
            password='testpassword123',
            first_name='Admin',
            last_name='User',
            role=User.ADMIN
        )
        
        self.teacher = User.objects.create_user(
            username='teacher_user',
            email='teacher@example.com',
            password='testpassword123',
            first_name='Teacher',
            last_name='User',
            role=User.TEACHER
        )
        
        self.student = User.objects.create_user(
            username='student_user',
            email='student@example.com',
            password='testpassword123',
            first_name='Student',
            last_name='User',
            role=User.STUDENT
        )
        
        # Create a test course
        self.course = Course.objects.create(
            title='Test Course',
            description='This is a test course',
            instructor=self.teacher,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=30)
        )
        
        # Create lessons for the course
        self.lesson1 = Lesson.objects.create(
            course=self.course,
            title='Lesson 1',
            content='Content for lesson 1',
            order=1
        )
        
        self.lesson2 = Lesson.objects.create(
            course=self.course,
            title='Lesson 2',
            content='Content for lesson 2',
            order=2
        )
        
        # Create a quiz for the course
        self.quiz = Quiz.objects.create(
            course=self.course,
            title='Test Quiz',
            total_marks=100
        )
        
        # Add questions to the quiz
        self.question1 = Question.objects.create(
            quiz=self.quiz,
            question_text='What is 2+2?',
            question_type=Question.MULTIPLE_CHOICE,
            correct_answer='4',
            options=json.dumps(['2', '3', '4', '5'])
        )
        
        self.question2 = Question.objects.create(
            quiz=self.quiz,
            question_text='Is Python a programming language?',
            question_type=Question.TRUE_FALSE,
            correct_answer='true'
        )
        
        # Create client
        self.client = Client()

class AuthenticationTest(LMSTestCase):
    """Test user authentication functionality"""
    
    def test_user_login(self):
        """Test user login functionality"""
        # Test successful login
        response = self.client.post(reverse('accounts:login'), {
            'username': 'student_user',
            'password': 'testpassword123'
        })
        self.assertRedirects(response, reverse('core:dashboard'))
        
        # Test failed login
        response = self.client.post(reverse('accounts:login'), {
            'username': 'student_user',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid username or password')
    
    def test_user_registration(self):
        """Test user registration functionality"""
        # Count users before registration
        user_count = User.objects.count()
        
        # Test successful registration
        response = self.client.post(reverse('accounts:register'), {
            'username': 'new_student',
            'email': 'new_student@example.com',
            'first_name': 'New',
            'last_name': 'Student',
            'role': User.STUDENT,
            'password1': 'securepassword123',
            'password2': 'securepassword123'
        })
        
        # Check if user was created
        self.assertEqual(User.objects.count(), user_count + 1)
        self.assertRedirects(response, reverse('core:dashboard'))
        
        # Test registration validation
        response = self.client.post(reverse('accounts:register'), {
            'username': 'new_student',  # Already exists
            'email': 'invalid_email',
            'password1': 'pass',
            'password2': 'different_pass'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form-error')  # There should be form errors

class CourseManagementTest(LMSTestCase):
    """Test course management functionality"""
    
    def test_course_creation(self):
        """Test course creation by teacher"""
        # Login as teacher
        self.client.login(username='teacher_user', password='testpassword123')
        
        # Count courses before creation
        course_count = Course.objects.count()
        
        # Create a new course
        response = self.client.post(reverse('courses:create_course'), {
            'title': 'New Test Course',
            'description': 'This is a new test course',
            'start_date': (timezone.now() + timedelta(days=1)).date().strftime('%Y-%m-%d'),
            'end_date': (timezone.now() + timedelta(days=30)).date().strftime('%Y-%m-%d')
        })
        
        # Check if course was created
        self.assertEqual(Course.objects.count(), course_count + 1)
        new_course = Course.objects.latest('id')
        self.assertEqual(new_course.title, 'New Test Course')
        self.assertEqual(new_course.instructor, self.teacher)
    
    def test_course_editing(self):
        """Test course editing by instructor"""
        # Login as teacher
        self.client.login(username='teacher_user', password='testpassword123')
        
        # Edit the course
        response = self.client.post(reverse('courses:edit_course', kwargs={'course_id': self.course.id}), {
            'title': 'Updated Course Title',
            'description': 'Updated course description',
            'start_date': self.course.start_date,
            'end_date': self.course.end_date
        })
        
        # Check if course was updated
        self.course.refresh_from_db()
        self.assertEqual(self.course.title, 'Updated Course Title')
        self.assertEqual(self.course.description, 'Updated course description')
    
    def test_unauthorized_course_access(self):
        """Test that students cannot create or edit courses"""
        # Login as student
        self.client.login(username='student_user', password='testpassword123')
        
        # Try to create a course
        response = self.client.get(reverse('courses:create_course'))
        self.assertEqual(response.status_code, 403)  # Forbidden
        
        # Try to edit a course
        response = self.client.get(reverse('courses:edit_course', kwargs={'course_id': self.course.id}))
        self.assertEqual(response.status_code, 403)  # Forbidden

class EnrollmentTest(LMSTestCase):
    """Test course enrollment functionality"""
    
    def test_student_enrollment(self):
        """Test student enrolling in a course"""
        # Login as student
        self.client.login(username='student_user', password='testpassword123')
        
        # Count enrollments before
        enrollment_count = Enrollment.objects.count()
        
        # Enroll in course
        response = self.client.post(reverse('courses:enroll_course', kwargs={'course_id': self.course.id}))
        
        # Check if enrollment was created
        self.assertEqual(Enrollment.objects.count(), enrollment_count + 1)
        
        # Check enrollment details
        enrollment = Enrollment.objects.get(user=self.student, course=self.course)
        self.assertEqual(enrollment.status, Enrollment.ENROLLED)
        
        # Try to enroll again (should fail)
        response = self.client.post(reverse('courses:enroll_course', kwargs={'course_id': self.course.id}))
        self.assertContains(response, 'already enrolled')

class LessonAccessTest(LMSTestCase):
    """Test lesson access functionality"""
    
    def setUp(self):
        super().setUp()
        # Create enrollment for student
        self.enrollment = Enrollment.objects.create(
            user=self.student,
            course=self.course,
            status=Enrollment.ENROLLED
        )
    
    def test_lesson_access(self):
        """Test student accessing lesson content"""
        # Login as student
        self.client.login(username='student_user', password='testpassword123')
        
        # Access lesson
        response = self.client.get(reverse('lessons:lesson_detail', kwargs={'lesson_id': self.lesson1.id}))
        
        # Check lesson content is accessible
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Content for lesson 1')
        
        # Check that progress was created
        progress = Progress.objects.get(user=self.student, lesson=self.lesson1)
        self.assertEqual(progress.status, Progress.IN_PROGRESS)
    
    def test_unauthorized_lesson_access(self):
        """Test that non-enrolled students cannot access lessons"""
        # Create another student
        other_student = User.objects.create_user(
            username='other_student',
            password='testpassword123',
            role=User.STUDENT
        )
        
        # Login as the other student (not enrolled)
        self.client.login(username='other_student', password='testpassword123')
        
        # Try to access lesson
        response = self.client.get(reverse('lessons:lesson_detail', kwargs={'lesson_id': self.lesson1.id}))
        
        # Should be redirected with an error message
        self.assertEqual(response.status_code, 302)

class QuizTest(LMSTestCase):
    """Test quiz functionality"""
    
    def setUp(self):
        super().setUp()
        # Create enrollment for student
        self.enrollment = Enrollment.objects.create(
            user=self.student,
            course=self.course,
            status=Enrollment.ENROLLED
        )
    
    def test_quiz_attempt_and_grading(self):
        """Test taking a quiz and automatic grading"""
        # Login as student
        self.client.login(username='student_user', password='testpassword123')
        
        # Access quiz
        response = self.client.get(reverse('quizzes:quiz_attempt', kwargs={'quiz_id': self.quiz.id}))
        self.assertEqual(response.status_code, 200)
        
        # Submit quiz answers
        response = self.client.post(reverse('quizzes:quiz_submit', kwargs={'quiz_id': self.quiz.id}), {
            f'question_{self.question1.id}': '4',  # Correct answer
            f'question_{self.question2.id}': 'true'  # Correct answer
        })
        
        # Check answers were recorded
        self.assertEqual(Answer.objects.count(), 2)
        
        # Check answers were graded correctly
        answer1 = Answer.objects.get(question=self.question1, user=self.student)
        self.assertTrue(answer1.is_correct)
        
        answer2 = Answer.objects.get(question=self.question2, user=self.student)
        self.assertTrue(answer2.is_correct)
        
        # Check total score
        expected_score = self.quiz.total_marks
        actual_score = answer1.marks_obtained + answer2.marks_obtained
        self.assertEqual(actual_score, expected_score)
        
        # Check redirect to results page
        self.assertRedirects(response, reverse('quizzes:quiz_results', kwargs={'quiz_id': self.quiz.id}))

class ProgressTrackingTest(LMSTestCase):
    """Test progress tracking functionality"""
    
    def setUp(self):
        super().setUp()
        # Create enrollment for student
        self.enrollment = Enrollment.objects.create(
            user=self.student,
            course=self.course,
            status=Enrollment.ENROLLED
        )
    
    def test_course_progress_tracking(self):
        """Test tracking student progress through a course"""
        # Login as student
        self.client.login(username='student_user', password='testpassword123')
        
        # Access progress page
        response = self.client.get(reverse('progress:course_progress', kwargs={'course_id': self.course.id}))
        self.assertEqual(response.status_code, 200)
        
        # Mark lesson as complete
        response = self.client.post(reverse('lessons:mark_lesson_complete', kwargs={'lesson_id': self.lesson1.id}))
        
        # Check if progress was updated
        progress = Progress.objects.get(user=self.student, lesson=self.lesson1)
        self.assertEqual(progress.status, Progress.COMPLETED)
        
        # Check course progress
        response = self.client.get(reverse('progress:course_progress', kwargs={'course_id': self.course.id}))
        self.assertContains(response, 'completion_percentage')

class CertificateTest(LMSTestCase):
    """Test certificate generation functionality"""
    
    def setUp(self):
        super().setUp()
        # Create enrollment for student
        self.enrollment = Enrollment.objects.create(
            user=self.student,
            course=self.course,
            status=Enrollment.ENROLLED
        )
        
        # Create completed progress for all lessons
        Progress.objects.create(
            user=self.student,
            lesson=self.lesson1,
            status=Progress.COMPLETED
        )
        
        Progress.objects.create(
            user=self.student,
            lesson=self.lesson2,
            status=Progress.COMPLETED
        )
        
        # Create successful quiz answers
        Answer.objects.create(
            user=self.student,
            question=self.question1,
            answer_text='4',
            is_correct=True,
            marks_obtained=self.quiz.total_marks / 2
        )
        
        Answer.objects.create(
            user=self.student,
            question=self.question2,
            answer_text='true',
            is_correct=True,
            marks_obtained=self.quiz.total_marks / 2
        )
    
    def test_certificate_generation(self):
        """Test certificate generation for completed course"""
        # Login as teacher
        self.client.login(username='teacher_user', password='testpassword123')
        
        # Generate certificate
        response = self.client.post(reverse('certificates:generate_certificate', kwargs={
            'course_id': self.course.id,
            'student_id': self.student.id
        }))
        
        # Check if certificate was created
        certificate = Certificate.objects.get(user=self.student, course=self.course)
        self.assertIsNotNone(certificate)
        self.assertIsNotNone(certificate.certificate_code)
        
        # Check if enrollment status was updated
        self.enrollment.refresh_from_db()
        self.assertEqual(self.enrollment.status, Enrollment.COMPLETED)

class APITest(LMSTestCase):
    """Test API functionality"""
    
    def test_api_endpoints(self):
        """Test API authentication and endpoints"""
        # Get JWT token
        response = self.client.post('/api/auth/login/', {
            'username': 'teacher_user',
            'password': 'testpassword123'
        })
        self.assertEqual(response.status_code, 200)
        token = response.json().get('token')
        self.assertIsNotNone(token)
        
        # Access courses API with token
        headers = {'HTTP_AUTHORIZATION': f'Bearer {token}'}
        response = self.client.get('/api/courses/', **headers)
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.json()), 1)