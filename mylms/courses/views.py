from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.db.models import Count, Avg, Sum
from .models import Course
from .forms import CourseForm
from enrollments.models import Enrollment
from enrollments.forms import EnrollmentForm
from progress.models import Progress
from lessons.models import Lesson
from quizzes.models import Quiz, Question, Answer
from accounts.models import User

# Student Views
def course_list(request):
    """List all available courses"""
    courses = Course.objects.all().select_related('instructor')
    
    # Check which courses the user is already enrolled in
    enrolled_courses = []
    if request.user.is_authenticated and request.user.is_student():
        enrolled_courses = Enrollment.objects.filter(
            user=request.user
        ).values_list('course_id', flat=True)
    
    context = {
        'courses': courses,
        'enrolled_courses': enrolled_courses
    }
    return render(request, 'courses/course_list.html', context)

@login_required
def course_detail(request, course_id):
    """View course details, lessons, and quizzes"""
    course = get_object_or_404(Course, id=course_id)
    
    # Check if the user is enrolled in the course
    is_enrolled = False
    enrollment = None
    
    if request.user.is_student():
        enrollment = Enrollment.objects.filter(
            user=request.user,
            course=course
        ).first()
        is_enrolled = enrollment is not None and enrollment.status == Enrollment.ENROLLED
    
    # Get lessons with progress if user is enrolled
    lessons = Lesson.objects.filter(course=course).order_by('order')
    lessons_with_progress = []
    
    if is_enrolled:
        for lesson in lessons:
            progress = Progress.objects.filter(
                user=request.user,
                lesson=lesson
            ).first()
            
            status = Progress.NOT_STARTED
            if progress:
                status = progress.status
            
            lessons_with_progress.append({
                'lesson': lesson,
                'status': status
            })
    
    # Get quizzes
    quizzes = Quiz.objects.filter(course=course)
    quizzes_with_status = []
    
    if is_enrolled:
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
            
            quizzes_with_status.append({
                'quiz': quiz,
                'status': status,
                'score': score,
                'max_score': quiz.total_marks
            })
    
    context = {
        'course': course,
        'is_enrolled': is_enrolled,
        'enrollment': enrollment,
        'lessons': lessons_with_progress if is_enrolled else lessons,
        'quizzes': quizzes_with_status if is_enrolled else quizzes,
        'is_instructor': request.user == course.instructor
    }
    return render(request, 'courses/course_detail.html', context)

@login_required
def enroll_course(request, course_id):
    """Enroll in a course"""
    if not request.user.is_student():
        messages.error(request, 'Only students can enroll in courses.')
        return redirect('courses:course_detail', course_id=course_id)
    
    course = get_object_or_404(Course, id=course_id)
    
    # Check if already enrolled
    if Enrollment.objects.filter(user=request.user, course=course).exists():
        messages.warning(request, 'You are already enrolled in this course.')
        return redirect('courses:course_detail', course_id=course_id)
    
    # Create enrollment
    enrollment = Enrollment.objects.create(
        user=request.user,
        course=course,
        status=Enrollment.ENROLLED
    )
    
    # Create notification
    from notifications.models import Notification
    Notification.objects.create(
        user=request.user,
        title=f"Enrollment Confirmation: {course.title}",
        message=f"You have successfully enrolled in the course: {course.title}",
        notification_type=Notification.ENROLLMENT
    )
    
    messages.success(request, f'You have successfully enrolled in {course.title}')
    return redirect('courses:course_detail', course_id=course_id)

# Teacher Views
@login_required
def teacher_dashboard(request):
    """Teacher dashboard with courses and statistics"""
    if not request.user.is_teacher() and not request.user.is_admin():
        return HttpResponseForbidden("Access denied")
    
    # Get courses created by this teacher
    if request.user.is_admin():
        courses = Course.objects.all()
    else:
        courses = Course.objects.filter(instructor=request.user)
    
    # Get enrollment statistics
    enrollments_data = {}
    for course in courses:
        enrollments = Enrollment.objects.filter(course=course)
        enrollments_data[course.id] = {
            'total': enrollments.count(),
            'active': enrollments.filter(status=Enrollment.ENROLLED).count(),
            'completed': enrollments.filter(status=Enrollment.COMPLETED).count(),
            'dropped': enrollments.filter(status=Enrollment.DROPPED).count(),
        }
    
    context = {
        'courses': courses,
        'enrollments_data': enrollments_data
    }
    return render(request, 'courses/teacher_dashboard.html', context)

@login_required
def create_course(request):
    """Create a new course"""
    if not request.user.is_teacher() and not request.user.is_admin():
        return HttpResponseForbidden("Access denied")
    
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.instructor = request.user
            course.save()
            messages.success(request, f'Course "{course.title}" has been created.')
            return redirect('courses:teacher_dashboard')
    else:
        form = CourseForm()
    
    context = {'form': form, 'action': 'Create'}
    return render(request, 'courses/course_form.html', context)

@login_required
def edit_course(request, course_id):
    """Edit an existing course"""
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user is the instructor or admin
    if course.instructor != request.user and not request.user.is_admin():
        return HttpResponseForbidden("Access denied")
    
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, f'Course "{course.title}" has been updated.')
            return redirect('courses:teacher_dashboard')
    else:
        form = CourseForm(instance=course)
    
    context = {'form': form, 'course': course, 'action': 'Edit'}
    return render(request, 'courses/course_form.html', context)

@login_required
def delete_course(request, course_id):
    """Delete a course"""
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user is the instructor or admin
    if course.instructor != request.user and not request.user.is_admin():
        return HttpResponseForbidden("Access denied")
    
    if request.method == 'POST':
        course_title = course.title
        course.delete()
        messages.success(request, f'Course "{course_title}" has been deleted.')
        return redirect('courses:teacher_dashboard')
    
    context = {'course': course}
    return render(request, 'courses/course_confirm_delete.html', context)

@login_required
def course_students(request, course_id):
    """View and manage students enrolled in a course"""
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user is the instructor or admin
    if course.instructor != request.user and not request.user.is_admin():
        return HttpResponseForbidden("Access denied")
    
    enrollments = Enrollment.objects.filter(course=course).select_related('user')
    
    # Process updates to enrollment status if submitted
    if request.method == 'POST':
        enrollment_id = request.POST.get('enrollment_id')
        new_status = request.POST.get('status')
        
        if enrollment_id and new_status:
            enrollment = get_object_or_404(Enrollment, id=enrollment_id, course=course)
            enrollment.status = new_status
            enrollment.save()
            messages.success(request, f'Status updated for {enrollment.user.username}')
    
    context = {
        'course': course,
        'enrollments': enrollments,
    }
    return render(request, 'courses/course_students.html', context)

@login_required
def course_statistics(request, course_id):
    """View detailed statistics for a course"""
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user is the instructor or admin
    if course.instructor != request.user and not request.user.is_admin():
        return HttpResponseForbidden("Access denied")
    
    # Enrollment statistics
    enrollments = Enrollment.objects.filter(course=course)
    enrollment_stats = {
        'total': enrollments.count(),
        'active': enrollments.filter(status=Enrollment.ENROLLED).count(),
        'completed': enrollments.filter(status=Enrollment.COMPLETED).count(),
        'dropped': enrollments.filter(status=Enrollment.DROPPED).count(),
    }
    
    # Lesson progress statistics
    lessons = Lesson.objects.filter(course=course)
    lesson_stats = []
    
    for lesson in lessons:
        progress_records = Progress.objects.filter(lesson=lesson)
        
        not_started = progress_records.filter(status=Progress.NOT_STARTED).count()
        in_progress = progress_records.filter(status=Progress.IN_PROGRESS).count()
        completed = progress_records.filter(status=Progress.COMPLETED).count()
        
        total = not_started + in_progress + completed
        completion_rate = (completed / total * 100) if total > 0 else 0
        
        lesson_stats.append({
            'lesson': lesson,
            'not_started': not_started,
            'in_progress': in_progress,
            'completed': completed,
            'completion_rate': completion_rate
        })
    
    # Quiz statistics
    quizzes = Quiz.objects.filter(course=course)
    quiz_stats = []
    
    for quiz in quizzes:
        questions = Question.objects.filter(quiz=quiz)
        
        # Calculate average score
        answers = Answer.objects.filter(question__in=questions)
        attempts = answers.values('user').distinct().count()
        
        # Group by user and sum marks to get each user's total score
        user_scores = answers.values('user').annotate(
            total_score=Sum('marks_obtained')
        )
        
        # Calculate average of these totals
        avg_score = 0
        if user_scores:
            avg_score = sum(score['total_score'] for score in user_scores) / len(user_scores)
        
        quiz_stats.append({
            'quiz': quiz,
            'attempts': attempts,
            'avg_score': avg_score,
            'max_score': quiz.total_marks,
            'avg_percentage': (avg_score / quiz.total_marks * 100) if quiz.total_marks > 0 else 0
        })
    
    context = {
        'course': course,
        'enrollment_stats': enrollment_stats,
        'lesson_stats': lesson_stats,
        'quiz_stats': quiz_stats,
    }
    return render(request, 'courses/course_statistics.html', context)