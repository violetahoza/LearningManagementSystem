from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.db.models import Count, Sum
from .models import Progress
from courses.models import Course
from lessons.models import Lesson
from quizzes.models import Quiz, Question, Answer
from enrollments.models import Enrollment
from accounts.models import User
from certificates.models import Certificate

@login_required
def course_progress(request, course_id):
    """View progress for a specific course"""
    if not request.user.is_student():
        return HttpResponseForbidden("Only students can access this page.")
    
    course = get_object_or_404(Course, id=course_id)
    
    # Check if enrolled
    enrollment = get_object_or_404(
        Enrollment, 
        user=request.user,
        course=course
    )
    
    # Get lessons with progress
    lessons = Lesson.objects.filter(course=course).order_by('order')
    
    lessons_progress = []
    total_completed = 0
    
    for lesson in lessons:
        progress = Progress.objects.filter(
            user=request.user,
            lesson=lesson
        ).first()
        
        status = Progress.NOT_STARTED
        if progress:
            status = progress.status
            if status == Progress.COMPLETED:
                total_completed += 1
        
        lessons_progress.append({
            'lesson': lesson,
            'status': status,
            'progress_id': progress.id if progress else None,
            'last_accessed': progress.last_accessed if progress else None
        })
    
    # Calculate overall progress
    total_lessons = lessons.count()
    completion_percentage = (total_completed / total_lessons * 100) if total_lessons > 0 else 0
    
    # Get quiz progress
    quizzes = Quiz.objects.filter(course=course)
    quizzes_progress = []
    
    for quiz in quizzes:
        questions = Question.objects.filter(quiz=quiz)
        answers = Answer.objects.filter(
            question__in=questions,
            user=request.user
        )
        
        total_questions = questions.count()
        answered_questions = answers.values('question').distinct().count()
        
        if answered_questions == 0:
            status = 'not_started'
        elif answered_questions < total_questions:
            status = 'in_progress'
        else:
            status = 'completed'
        
        # Calculate score if completed
        score = 0
        if status == 'completed':
            score = answers.aggregate(Sum('marks_obtained'))['marks_obtained__sum'] or 0
        
        quizzes_progress.append({
            'quiz': quiz,
            'status': status,
            'answered': answered_questions,
            'total': total_questions,
            'score': score,
            'max_score': quiz.total_marks,
            'percentage': (score / quiz.total_marks * 100) if quiz.total_marks > 0 else 0
        })
    
    # Check if course is completed and certificate issued
    is_completed = completion_percentage == 100 and all(q['status'] == 'completed' for q in quizzes_progress)
    certificate = None
    
    if is_completed:
        # Update enrollment status if needed
        if enrollment.status != Enrollment.COMPLETED:
            enrollment.status = Enrollment.COMPLETED
            enrollment.save()
        
        # Check for certificate
        certificate = Certificate.objects.filter(
            user=request.user,
            course=course
        ).first()
    
    context = {
        'course': course,
        'enrollment': enrollment,
        'lessons_progress': lessons_progress,
        'quizzes_progress': quizzes_progress,
        'completion_percentage': completion_percentage,
        'is_completed': is_completed,
        'certificate': certificate
    }
    
    return render(request, 'progress/course_progress.html', context)

@login_required
def update_progress(request, progress_id):
    """Update progress status"""
    if not request.user.is_student():
        return HttpResponseForbidden("Only students can update progress.")
    
    progress = get_object_or_404(Progress, id=progress_id, user=request.user)
    lesson = progress.lesson
    course = lesson.course
    
    # Check if enrolled
    enrollment = get_object_or_404(
        Enrollment, 
        user=request.user,
        course=course,
        status=Enrollment.ENROLLED
    )
    
    if request.method == 'POST':
        status = request.POST.get('status')
        
        if status in [Progress.NOT_STARTED, Progress.IN_PROGRESS, Progress.COMPLETED]:
            progress.status = status
            progress.save()
            messages.success(request, f'Progress updated for "{lesson.title}"')
        else:
            messages.error(request, 'Invalid status')
    
    return redirect('progress:course_progress', course_id=course.id)

@login_required
def student_progress(request, student_id, course_id):
    """View progress for a specific student in a course (teacher view)"""
    if not request.user.is_teacher() and not request.user.is_admin():
        return HttpResponseForbidden("Access denied")
    
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user is the instructor or admin
    if course.instructor != request.user and not request.user.is_admin():
        return HttpResponseForbidden("Access denied")
    
    student = get_object_or_404(User, id=student_id, role=User.STUDENT)
    
    # Check if student is enrolled
    enrollment = get_object_or_404(
        Enrollment, 
        user=student,
        course=course
    )
    
    # Get lessons with progress
    lessons = Lesson.objects.filter(course=course).order_by('order')
    
    lessons_progress = []
    total_completed = 0
    
    for lesson in lessons:
        progress = Progress.objects.filter(
            user=student,
            lesson=lesson
        ).first()
        
        status = Progress.NOT_STARTED
        if progress:
            status = progress.status
            if status == Progress.COMPLETED:
                total_completed += 1
        
        lessons_progress.append({
            'lesson': lesson,
            'status': status,
            'last_accessed': progress.last_accessed if progress else None
        })
    
    # Calculate overall progress
    total_lessons = lessons.count()
    completion_percentage = (total_completed / total_lessons * 100) if total_lessons > 0 else 0
    
    # Get quiz progress
    quizzes = Quiz.objects.filter(course=course)
    quizzes_progress = []
    
    for quiz in quizzes:
        questions = Question.objects.filter(quiz=quiz)
        answers = Answer.objects.filter(
            question__in=questions,
            user=student
        )
        
        total_questions = questions.count()
        answered_questions = answers.values('question').distinct().count()
        
        if answered_questions == 0:
            status = 'not_started'
        elif answered_questions < total_questions:
            status = 'in_progress'
        else:
            status = 'completed'
        
        # Calculate score if completed
        score = 0
        if status == 'completed':
            score = answers.aggregate(Sum('marks_obtained'))['marks_obtained__sum'] or 0
        
        quizzes_progress.append({
            'quiz': quiz,
            'status': status,
            'answered': answered_questions,
            'total': total_questions,
            'score': score,
            'max_score': quiz.total_marks,
            'percentage': (score / quiz.total_marks * 100) if quiz.total_marks > 0 else 0
        })
    
    # Check for certificate
    certificate = Certificate.objects.filter(
        user=student,
        course=course
    ).first()
    
    context = {
        'course': course,
        'student': student,
        'enrollment': enrollment,
        'lessons_progress': lessons_progress,
        'quizzes_progress': quizzes_progress,
        'completion_percentage': completion_percentage,
        'certificate': certificate
    }
    
    return render(request, 'progress/student_progress.html', context)