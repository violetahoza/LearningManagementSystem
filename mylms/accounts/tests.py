from django.test import TestCase, Client
from django.urls import reverse
from django.db.models import Sum
import json
from accounts.models import User
from courses.models import Course
from enrollments.models import Enrollment
from .models import Quiz, Question, Answer
from datetime import date, timedelta

class QuizModelTest(TestCase):
    """Test case for Quiz and Question models"""
    
    def setUp(self):
        self.teacher = User.objects.create_user(
            username='teacher',
            password='password123',
            email='teacher@example.com',
            role=User.TEACHER
        )
        
        self.course = Course.objects.create(
            title='Test Course',
            description='This is a test course',
            instructor=self.teacher,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30)
        )
        
        self.quiz = Quiz.objects.create(
            course=self.course,
            title='Test Quiz',
            total_marks=100
        )
        
        # Create different types of questions
        self.mcq = Question.objects.create(
            quiz=self.quiz,
            question_text='Multiple choice question',
            question_type=Question.MULTIPLE_CHOICE,
            correct_answer='Option A',
            options=json.dumps(['Option A', 'Option B', 'Option C', 'Option D'])
        )
        
        self.tf = Question.objects.create(
            quiz=self.quiz,
            question_text='True/False question',
            question_type=Question.TRUE_FALSE,
            correct_answer='true'
        )
        
        self.sa = Question.objects.create(
            quiz=self.quiz,
            question_text='Short answer question',
            question_type=Question.SHORT_ANSWER,
            correct_answer='Python'
        )
    
    def test_quiz_creation(self):
        """Test that quiz is created correctly"""
        self.assertEqual(Quiz.objects.count(), 1)
        self.assertEqual(self.quiz.title, 'Test Quiz')
        self.assertEqual(self.quiz.course, self.course)
    
    def test_question_creation(self):
        """Test that questions are created correctly"""
        self.assertEqual(Question.objects.count(), 3)
        self.assertEqual(self.mcq.question_type, Question.MULTIPLE_CHOICE)
        self.assertEqual(self.tf.question_type, Question.TRUE_FALSE)
        self.assertEqual(self.sa.question_type, Question.SHORT_ANSWER)
    
    def test_string_representation(self):
        """Test string representation of Quiz and Question models"""
        self.assertEqual(str(self.quiz), 'Test Quiz')
        self.assertEqual(str(self.mcq), 'Multiple choice question')

class QuizViewsTest(TestCase):
    """Test case for Quiz views"""
    
    def setUp(self):
        self.client = Client()
        
        # Create users
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
        
        # Enroll student in course
        self.enrollment = Enrollment.objects.create(
            user=self.student,
            course=self.course,
            status=Enrollment.ENROLLED
        )
        
        # Create quiz
        self.quiz = Quiz.objects.create(
            course=self.course,
            title='Test Quiz',
            total_marks=100
        )
        
        # Create questions
        self.mcq = Question.objects.create(
            quiz=self.quiz,
            question_text='Which of these is a programming language?',
            question_type=Question.MULTIPLE_CHOICE,
            correct_answer='Python',
            options=json.dumps(['HTML', 'CSS', 'Python', 'MySQL'])
        )
        
        self.tf = Question.objects.create(
            quiz=self.quiz,
            question_text='Python is a programming language.',
            question_type=Question.TRUE_FALSE,
            correct_answer='true'
        )
    
    def test_quiz_detail_view(self):
        """Test quiz detail view"""
        # Unauthenticated user
        response = self.client.get(reverse('quizzes:quiz_detail', kwargs={'quiz_id': self.quiz.id}))
        self.assertRedirects(response, f'/accounts/login/?next={reverse("quizzes:quiz_detail", kwargs={"quiz_id": self.quiz.id})}')
        
        # Teacher
        self.client.login(username='teacher', password='password123')
        response = self.client.get(reverse('quizzes:quiz_detail', kwargs={'quiz_id': self.quiz.id}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'quizzes/quiz_detail.html')
        self.assertContains(response, 'Test Quiz')
        
        # Student
        self.client.login(username='student', password='password123')
        response = self.client.get(reverse('quizzes:quiz_detail', kwargs={'quiz_id': self.quiz.id}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'quizzes/quiz_detail.html')
        self.assertContains(response, 'Test Quiz')
    
    def test_create_quiz_auth(self):
        """Test that only teachers can create quizzes"""
        url = reverse('quizzes:create_quiz', kwargs={'course_id': self.course.id})
        
        # Unauthenticated user
        response = self.client.get(url)
        self.assertRedirects(response, f'/accounts/login/?next={url}')
        
        # Student
        self.client.login(username='student', password='password123')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)  # Forbidden
        
        # Teacher
        self.client.login(username='teacher', password='password123')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'quizzes/quiz_form.html')
    
    def test_quiz_attempt_auth(self):
        """Test that only enrolled students can attempt quizzes"""
        url = reverse('quizzes:quiz_attempt', kwargs={'quiz_id': self.quiz.id})
        
        # Unauthenticated user
        response = self.client.get(url)
        self.assertRedirects(response, f'/accounts/login/?next={url}')
        
        # Teacher
        self.client.login(username='teacher', password='password123')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)  # Forbidden
        
        # Student
        self.client.login(username='student', password='password123')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'quizzes/quiz_attempt.html')