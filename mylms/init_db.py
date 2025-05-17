#!/usr/bin/env python
"""
Script to initialize the database with sample data.
"""

import os
import sys
import django
import random
from datetime import timedelta

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mylms.settings')
django.setup()

# Import models
from django.utils import timezone
from accounts.models import User
from courses.models import Course
from lessons.models import Lesson
from quizzes.models import Quiz, Question, Answer
from enrollments.models import Enrollment
from progress.models import Progress
from certificates.models import Certificate
from notifications.models import Notification

def create_admin_user():
    """
    Create an admin user if one doesn't already exist.
    """
    # Check if an admin user already exists
    if User.objects.filter(role=User.ADMIN).exists():
        print("Admin user already exists.")
        admin_user = User.objects.filter(role=User.ADMIN).first()
        print(f"Username: {admin_user.username}")
        return
    
    # Create the admin user
    username = 'admin'
    email = 'admin@example.com'
    password = 'admin123'  
    
    # Create the user
    admin_user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name='Admin',
        last_name='User',
        role=User.ADMIN,
    )
    
    admin_user.is_staff = True  # For Django admin access
    admin_user.is_superuser = True  # Full Django admin permissions
    admin_user.save()
    
    print(f"Admin user created successfully.")
    print(f"Username: {username}")
    print(f"Password: {password}")
    print(f"Email: {email}")
    print("Note: This is a testing account. Please change the password in production!")


def create_sample_users():
    """Create sample users for testing"""
    print("Creating sample users...")
    
    # Create teachers
    teachers = []
    for i in range(1, 4):
        username = f"teacher{i}"
        if not User.objects.filter(username=username).exists():
            teacher = User.objects.create_user(
                username=username,
                email=f"teacher{i}@example.com",
                password=f"teacher{i}123",  # Test password, change in production!
                first_name=f"Teacher{i}",
                last_name="User",
                role=User.TEACHER
            )
            teachers.append(teacher)
            print(f"Created teacher: {username}")
        else:
            teachers.append(User.objects.get(username=username))
            print(f"Teacher already exists: {username}")
    
    # Create students
    students = []
    for i in range(1, 11):
        username = f"student{i}"
        if not User.objects.filter(username=username).exists():
            student = User.objects.create_user(
                username=username,
                email=f"student{i}@example.com",
                password=f"student{i}123",  # Test password, change in production!
                first_name=f"Student{i}",
                last_name="User",
                role=User.STUDENT
            )
            students.append(student)
            print(f"Created student: {username}")
        else:
            students.append(User.objects.get(username=username))
            print(f"Student already exists: {username}")
    
    return teachers, students

def create_sample_courses(teachers):
    """Create sample courses for testing"""
    print("\nCreating sample courses...")
    
    courses = []
    course_data = [
        {
            'title': 'Introduction to Python Programming',
            'description': 'A beginner-friendly course to learn Python programming from scratch. You will learn basic concepts, data structures, and write your first Python applications.',
            'start_date': timezone.now().date() - timedelta(days=30),
            'end_date': timezone.now().date() + timedelta(days=60),
            'instructor': teachers[0]
        },
        {
            'title': 'Web Development with Django',
            'description': 'Learn how to build web applications using the Django framework. This course covers models, views, templates, forms, and deploying your application.',
            'start_date': timezone.now().date() - timedelta(days=15),
            'end_date': timezone.now().date() + timedelta(days=75),
            'instructor': teachers[0]
        },
        {
            'title': 'Data Science Fundamentals',
            'description': 'An introduction to data science using Python. Learn about data analysis, visualization, and machine learning basics.',
            'start_date': timezone.now().date() + timedelta(days=15),
            'end_date': timezone.now().date() + timedelta(days=105),
            'instructor': teachers[1]
        },
        {
            'title': 'Advanced JavaScript',
            'description': 'Take your JavaScript skills to the next level. Learn about modern features, frameworks, and best practices for front-end development.',
            'start_date': timezone.now().date() - timedelta(days=60),
            'end_date': timezone.now().date() - timedelta(days=10),
            'instructor': teachers[1]
        },
        {
            'title': 'Database Design and SQL',
            'description': 'Learn how to design efficient databases and write complex SQL queries. This course covers relational database concepts, normalization, and performance optimization.',
            'start_date': timezone.now().date() - timedelta(days=5),
            'end_date': timezone.now().date() + timedelta(days=85),
            'instructor': teachers[2]
        },
    ]
    
    for data in course_data:
        # Check if course already exists
        if not Course.objects.filter(title=data['title']).exists():
            course = Course.objects.create(**data)
            courses.append(course)
            print(f"Created course: {course.title}")
        else:
            course = Course.objects.get(title=data['title'])
            courses.append(course)
            print(f"Course already exists: {course.title}")
    
    return courses

def create_sample_lessons(courses):
    """Create sample lessons for each course"""
    print("\nCreating sample lessons...")
    
    lessons = []
    
    for course in courses:
        # Different number of lessons for each course
        num_lessons = random.randint(5, 8)
        
        # Check if course already has lessons
        existing_lessons = Lesson.objects.filter(course=course).count()
        if existing_lessons > 0:
            print(f"Course '{course.title}' already has {existing_lessons} lessons.")
            lessons.extend(Lesson.objects.filter(course=course))
            continue
        
        for i in range(1, num_lessons + 1):
            # Create lesson based on course subject
            if "Python" in course.title:
                lesson_titles = [
                    "Getting Started with Python",
                    "Variables and Data Types",
                    "Control Flow: Conditionals and Loops",
                    "Functions and Modules",
                    "Working with Lists and Dictionaries",
                    "File Handling in Python",
                    "Object-Oriented Programming",
                    "Exception Handling"
                ]
                content_prefix = "Python programming lesson content: "
                
            elif "Django" in course.title:
                lesson_titles = [
                    "Setting Up Django Environment",
                    "Creating Your First Django Project",
                    "Models and Database Migrations",
                    "Views and URL Routing",
                    "Templates and Static Files",
                    "Forms and User Input",
                    "Authentication and Authorization",
                    "REST API with Django Rest Framework"
                ]
                content_prefix = "Django web development lesson content: "
                
            elif "Data Science" in course.title:
                lesson_titles = [
                    "Introduction to Data Science",
                    "Data Collection and Cleaning",
                    "Exploratory Data Analysis",
                    "Data Visualization with Matplotlib",
                    "Statistical Analysis with NumPy",
                    "Pandas for Data Manipulation",
                    "Introduction to Machine Learning",
                    "Building Your First ML Model"
                ]
                content_prefix = "Data science lesson content: "
                
            elif "JavaScript" in course.title:
                lesson_titles = [
                    "ES6+ Features and Syntax",
                    "Promises and Async/Await",
                    "DOM Manipulation",
                    "Event Handling",
                    "Working with APIs",
                    "JavaScript Frameworks Overview",
                    "Testing JavaScript Applications",
                    "Performance Optimization"
                ]
                content_prefix = "JavaScript programming lesson content: "
                
            else:  # Database course
                lesson_titles = [
                    "Introduction to Databases",
                    "Relational Database Concepts",
                    "SQL Basics: SELECT, INSERT, UPDATE, DELETE",
                    "Advanced Queries and Joins",
                    "Database Design and Normalization",
                    "Indexes and Performance Optimization",
                    "Transactions and Concurrency",
                    "NoSQL Databases Introduction"
                ]
                content_prefix = "Database design lesson content: "
            
            # Create lessons up to the number we decided for this course
            if i <= len(lesson_titles):
                title = lesson_titles[i-1]
                content = f"{content_prefix} This is the content for {title}. It includes explanations, examples, and practice exercises."
                
                # Add more detailed content based on the lesson
                content += "\n\n## Lesson Objectives\n\n"
                content += "- Understand key concepts\n"
                content += "- Apply knowledge through examples\n"
                content += "- Complete practice exercises\n\n"
                content += "## Lesson Content\n\n"
                content += "This section contains detailed explanations of the concepts covered in this lesson. "
                content += "You'll find code examples, diagrams, and thorough explanations to help you understand the material.\n\n"
                content += "## Practice Exercises\n\n"
                content += "1. First exercise description\n"
                content += "2. Second exercise description\n"
                content += "3. Third exercise description\n\n"
                content += "## Additional Resources\n\n"
                content += "- Link to resource 1\n"
                content += "- Link to resource 2\n"
                
                # Add a video URL for some lessons
                video_url = None
                if i % 3 == 0:  # Add video URL for every third lesson
                    video_url = "https://www.youtube.com/embed/dQw4w9WgXcQ"  # Placeholder video URL
                
                lesson = Lesson.objects.create(
                    course=course,
                    title=title,
                    content=content,
                    video_url=video_url,
                    order=i
                )
                lessons.append(lesson)
                print(f"Created lesson: {lesson.title} (Course: {course.title})")
    
    return lessons

def create_sample_quizzes(courses):
    """Create sample quizzes for each course"""
    print("\nCreating sample quizzes...")
    
    quizzes = []
    
    for course in courses:
        # Check if course already has quizzes
        existing_quizzes = Quiz.objects.filter(course=course).count()
        if existing_quizzes > 0:
            print(f"Course '{course.title}' already has {existing_quizzes} quizzes.")
            quizzes.extend(Quiz.objects.filter(course=course))
            continue
        
        # Create 1-2 quizzes per course
        num_quizzes = random.randint(1, 2)
        
        for i in range(1, num_quizzes + 1):
            quiz_title = f"Quiz {i}: " + ("Mid-term Assessment" if i == 1 else "Final Assessment")
            
            quiz = Quiz.objects.create(
                course=course,
                title=quiz_title,
                total_marks=100
            )
            quizzes.append(quiz)
            print(f"Created quiz: {quiz.title} (Course: {course.title})")
            
            # Create questions for the quiz
            create_sample_questions(quiz, course.title)
    
    return quizzes

def create_sample_questions(quiz, course_title):
    """Create sample questions for a quiz"""
    
    # Define different question sets based on course subject
    if "Python" in course_title:
        questions_data = [
            {
                'question_text': 'What is the correct way to define a function in Python?',
                'question_type': Question.MULTIPLE_CHOICE,
                'options': '["def function_name():", "function function_name():", "function_name():", "define function_name():"]',
                'correct_answer': 'def function_name():'
            },
            {
                'question_text': 'Which of the following data types is mutable in Python?',
                'question_type': Question.MULTIPLE_CHOICE,
                'options': '["String", "Tuple", "List", "Integer"]',
                'correct_answer': 'List'
            },
            {
                'question_text': 'What does the following code output? print(2**3)',
                'question_type': Question.MULTIPLE_CHOICE,
                'options': '["8", "6", "5", "Error"]',
                'correct_answer': '8'
            },
            {
                'question_text': 'Python is a case-sensitive language.',
                'question_type': Question.TRUE_FALSE,
                'options': None,
                'correct_answer': 'true'
            },
            {
                'question_text': 'What built-in function converts an integer to a string in Python?',
                'question_type': Question.SHORT_ANSWER,
                'options': None,
                'correct_answer': 'str'
            }
        ]
    elif "Django" in course_title:
        questions_data = [
            {
                'question_text': 'What command is used to create a new Django project?',
                'question_type': Question.MULTIPLE_CHOICE,
                'options': '["django-admin startproject", "django-admin createproject", "python manage.py newproject", "python manage.py startproject"]',
                'correct_answer': 'django-admin startproject'
            },
            {
                'question_text': 'In Django, what does the models.py file contain?',
                'question_type': Question.MULTIPLE_CHOICE,
                'options': '["URL patterns", "Database structure definitions", "View functions", "Template definitions"]',
                'correct_answer': 'Database structure definitions'
            },
            {
                'question_text': 'Which of the following is NOT a valid Django template tag?',
                'question_type': Question.MULTIPLE_CHOICE,
                'options': '["{% if %}", "{% for %}", "{% while %}", "{% include %}"]',
                'correct_answer': '{% while %}'
            },
            {
                'question_text': 'Django follows the MVT architectural pattern.',
                'question_type': Question.TRUE_FALSE,
                'options': None,
                'correct_answer': 'true'
            },
            {
                'question_text': 'What command is used to run database migrations in Django?',
                'question_type': Question.SHORT_ANSWER,
                'options': None,
                'correct_answer': 'python manage.py migrate'
            }
        ]
    else:  # Generic questions for other courses
        questions_data = [
            {
                'question_text': 'Which of the following is NOT a primary consideration in course design?',
                'question_type': Question.MULTIPLE_CHOICE,
                'options': '["Learning objectives", "Student assessment", "Instructor preference", "Student needs"]',
                'correct_answer': 'Instructor preference'
            },
            {
                'question_text': 'What is the purpose of formative assessment?',
                'question_type': Question.MULTIPLE_CHOICE,
                'options': '["To grade students", "To provide feedback during learning", "To evaluate teaching methods", "To rank students"]',
                'correct_answer': 'To provide feedback during learning'
            },
            {
                'question_text': 'Which learning theory emphasizes the importance of social interaction in learning?',
                'question_type': Question.MULTIPLE_CHOICE,
                'options': '["Behaviorism", "Cognitivism", "Constructivism", "Social Constructivism"]',
                'correct_answer': 'Social Constructivism'
            },
            {
                'question_text': 'Online learning is always less effective than face-to-face learning.',
                'question_type': Question.TRUE_FALSE,
                'options': None,
                'correct_answer': 'false'
            },
            {
                'question_text': 'What does LMS stand for in the context of this course?',
                'question_type': Question.SHORT_ANSWER,
                'options': None,
                'correct_answer': 'Learning Management System'
            }
        ]
    
    # Create questions
    for data in questions_data:
        question = Question.objects.create(
            quiz=quiz,
            question_text=data['question_text'],
            question_type=data['question_type'],
            options=data['options'],
            correct_answer=data['correct_answer']
        )
        print(f"  Created question: {question.question_text[:30]}...")

def create_enrollments(students, courses):
    """Create sample enrollments"""
    print("\nCreating sample enrollments...")
    
    enrollments = []
    
    # Each student enrolls in 1-3 courses randomly
    for student in students:
        # Shuffle courses for random selection
        available_courses = list(courses)
        random.shuffle(available_courses)
        
        # Determine how many courses this student will take (1-3)
        num_courses = random.randint(1, min(3, len(available_courses)))
        
        for i in range(num_courses):
            course = available_courses[i]
            
            # Skip if already enrolled
            if Enrollment.objects.filter(user=student, course=course).exists():
                print(f"Student {student.username} is already enrolled in {course.title}")
                continue
            
            # Determine enrollment status (mostly enrolled, some completed)
            status = Enrollment.ENROLLED
            if random.random() < 0.3:  # 30% chance of completed
                status = Enrollment.COMPLETED
            
            enrollment = Enrollment.objects.create(
                user=student,
                course=course,
                status=status,
                enrolled_at=timezone.now() - timedelta(days=random.randint(1, 30))
            )
            
            enrollments.append(enrollment)
            print(f"Enrolled {student.username} in {course.title} (Status: {status})")
            
            # Create progress records for this enrollment
            if status == Enrollment.ENROLLED:
                create_progress_records(student, course)
            elif status == Enrollment.COMPLETED:
                create_completed_progress(student, course)
                
                # Create certificate for completed courses
                create_certificate(student, course)
    
    return enrollments

def create_progress_records(student, course):
    """Create progress records for enrolled student"""
    lessons = Lesson.objects.filter(course=course).order_by('order')
    
    # Complete some lessons, leave others in progress
    for i, lesson in enumerate(lessons):
        if i < len(lessons) / 3:  # First third: completed
            status = Progress.COMPLETED
        elif i < len(lessons) * 2 / 3:  # Middle third: in progress
            status = Progress.IN_PROGRESS
        else:  # Last third: not started
            status = Progress.NOT_STARTED
        
        Progress.objects.create(
            user=student,
            lesson=lesson,
            status=status
        )

def create_completed_progress(student, course):
    """Create completed progress records for all lessons"""
    lessons = Lesson.objects.filter(course=course)
    
    for lesson in lessons:
        Progress.objects.create(
            user=student,
            lesson=lesson,
            status=Progress.COMPLETED
        )
    
    # Also create completed quiz answers
    quizzes = Quiz.objects.filter(course=course)
    for quiz in quizzes:
        questions = Question.objects.filter(quiz=quiz)
        
        for question in questions:
            # Most answers are correct (this is a completed course)
            is_correct = random.random() < 0.9  # 90% chance of correct answer
            
            if is_correct:
                answer_text = question.correct_answer
                marks = quiz.total_marks / questions.count()
            else:
                # Generate incorrect answer
                if question.question_type == Question.MULTIPLE_CHOICE and question.options:
                    import json
                    options = json.loads(question.options)
                    options.remove(question.correct_answer)
                    answer_text = random.choice(options)
                elif question.question_type == Question.TRUE_FALSE:
                    answer_text = 'false' if question.correct_answer == 'true' else 'true'
                else:
                    answer_text = "Wrong answer"
                
                marks = 0
            
            Answer.objects.create(
                question=question,
                user=student,
                answer_text=answer_text,
                is_correct=is_correct,
                marks_obtained=marks
            )

def create_certificate(student, course):
    """Create certificate for completed course"""
    # Skip if certificate already exists
    if Certificate.objects.filter(user=student, course=course).exists():
        return
    
    certificate = Certificate.objects.create(
        user=student,
        course=course
    )
    
    # Create notification for certificate
    Notification.objects.create(
        user=student,
        title=f"Certificate Issued: {course.title}",
        message=f"Congratulations! You have been issued a certificate for completing {course.title}.",
        notification_type=Notification.CERTIFICATE_ISSUED
    )
    
    print(f"Created certificate for {student.username} - {course.title}")

def create_notifications():
    """Create sample notifications"""
    print("\nCreating sample notifications...")
    
    # System-wide notification for all students
    students = User.objects.filter(role=User.STUDENT)
    for student in students:
        # Welcome notification
        if not Notification.objects.filter(user=student, title__contains="Welcome").exists():
            Notification.objects.create(
                user=student,
                title="Welcome to the Learning Management System",
                message="Thank you for joining our learning platform. We're excited to have you on board!",
                notification_type=Notification.GENERAL,
                created_at=timezone.now() - timedelta(days=random.randint(1, 5))
            )
        
        # New course notification
        if not Notification.objects.filter(user=student, title__contains="New Course").exists():
            Notification.objects.create(
                user=student,
                title="New Course Available",
                message="A new course 'Advanced Machine Learning' will be available soon. Stay tuned!",
                notification_type=Notification.GENERAL,
                created_at=timezone.now() - timedelta(days=random.randint(1, 3))
            )
    
    print(f"Created notifications for {students.count()} students")

def main():
    """Main function to initialize the database with sample data"""
    print("Initializing database with sample data...\n")

    # Create admin user
    admin = create_admin_user()
    
    # Create users
    teachers, students = create_sample_users()
    
    # Create courses
    courses = create_sample_courses(teachers)
    
    # Create lessons
    lessons = create_sample_lessons(courses)
    
    # Create quizzes and questions
    quizzes = create_sample_quizzes(courses)
    
    # Create enrollments, progress, and certificates
    enrollments = create_enrollments(students, courses)
    
    # Create notifications
    create_notifications()
    
    print("\nDatabase initialization complete!")
    print(f"Created admin user: {admin.username}")
    print(f"Created {len(teachers)} teachers and {len(students)} students")
    print(f"Created {len(courses)} courses, {len(lessons)} lessons, and {len(quizzes)} quizzes")
    print(f"Created {len(enrollments)} enrollments")
    print(f"Created {Certificate.objects.count()} certificates")
    print(f"Created {Notification.objects.count()} notifications")
    
    print("\nYou can now log in with the following accounts:")
    print("Admin: username=admin, password=admin123")
    for i, teacher in enumerate(teachers, 1):
        print(f"Teacher {i}: username={teacher.username}, password={teacher.username}123")
    for i, student in enumerate(students, 1):
        print(f"Student {i}: username={student.username}, password={student.username}123")

if __name__ == '__main__':
    main()