from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, Q
from django.utils import timezone
import logging

from courses.models import Course
from enrollments.models import Enrollment
from certificates.models import Certificate
from notifications.models import Notification
from progress.models import Progress
from accounts.models import User

# Get logger
logger = logging.getLogger('user_activity')

def home(request):
    """Home page view"""
    # Get featured courses (e.g., most popular courses)
    featured_courses = Course.objects.annotate(
        students_count=Count('enrollments')
    ).order_by('-students_count')[:4]
    
    # Get recent courses
    recent_courses = Course.objects.filter(
        start_date__gte=timezone.now().date()
    ).order_by('start_date')[:4]
    
    context = {
        'featured_courses': featured_courses,
        'recent_courses': recent_courses,
    }
    return render(request, 'core/home.html', context)

@login_required
def dashboard(request):
    """Dashboard view - redirects to appropriate dashboard based on user role"""
    user = request.user
    logger.info(f"User {user.username} (ID: {user.id}) accessed dashboard")
    
    if user.is_admin():
        return admin_dashboard(request)
    elif user.is_teacher():
        return redirect('courses:teacher_dashboard')
    else:  # student
        return student_dashboard(request)

def admin_dashboard(request):
    """Admin dashboard view"""
    # Get system statistics
    total_courses = Course.objects.count()
    total_students = User.objects.filter(role=User.STUDENT).count()
    total_teachers = User.objects.filter(role=User.TEACHER).count()
    total_enrollments = Enrollment.objects.count()
    
    # Active courses (current date falls between start and end date)
    active_courses = Course.objects.filter(
        start_date__lte=timezone.now().date(),
        end_date__gte=timezone.now().date()
    ).count()
    
    # Courses starting soon (within next 7 days)
    next_week = timezone.now().date() + timezone.timedelta(days=7)
    upcoming_courses = Course.objects.filter(
        start_date__gt=timezone.now().date(),
        start_date__lte=next_week
    ).count()
    
    # Recently registered users (last 30 days)
    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
    recent_users = User.objects.filter(date_joined__gte=thirty_days_ago).count()
    
    # Course completion rate
    completed_enrollments = Enrollment.objects.filter(status=Enrollment.COMPLETED).count()
    completion_rate = (completed_enrollments / total_enrollments * 100) if total_enrollments > 0 else 0
    
    # Recent enrollments
    recent_enrollments = Enrollment.objects.all().order_by('-enrolled_at')[:10]
    
    # Recent certificates
    recent_certificates = Certificate.objects.all().order_by('-issue_date')[:10]
    
    context = {
        'total_courses': total_courses,
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_enrollments': total_enrollments,
        'active_courses': active_courses,
        'upcoming_courses': upcoming_courses,
        'recent_users': recent_users,
        'completion_rate': round(completion_rate, 1),
        'recent_enrollments': recent_enrollments,
        'recent_certificates': recent_certificates,
    }
    return render(request, 'admin/dashboard.html', context)

def student_dashboard(request):
    """Student dashboard view"""
    user = request.user
    
    # Get enrolled courses for student dashboard
    enrolled_courses = Enrollment.objects.filter(
        user=user, 
        status=Enrollment.ENROLLED
    ).select_related('course')
    
    # Add progress percentage to each enrollment
    for enrollment in enrolled_courses:
        course = enrollment.course
        lessons = course.lessons.all()
        total_lessons = lessons.count()
        
        if total_lessons > 0:
            completed_lessons = Progress.objects.filter(
                user=user,
                lesson__course=course,
                status=Progress.COMPLETED
            ).count()
            
            progress_percentage = (completed_lessons / total_lessons) * 100
        else:
            progress_percentage = 0
        
        enrollment.progress_percentage = progress_percentage
    
    # Get completed courses count
    completed_courses = Enrollment.objects.filter(
        user=user, 
        status=Enrollment.COMPLETED
    ).count()
    
    # Get certificates
    certificates = Certificate.objects.filter(user=user).select_related('course')[:3]
    certificates_count = certificates.count()
    
    # Calculate average progress
    if enrolled_courses:
        average_progress = sum([e.progress_percentage for e in enrolled_courses]) / len(enrolled_courses)
    else:
        average_progress = 0
    
    # Get recent notifications
    recent_notifications = Notification.objects.filter(user=user).order_by('-created_at')[:5]
    
    # Recommended courses - based on current enrollments
    # Get subjects of current courses
    enrolled_course_ids = [e.course.id for e in enrolled_courses]
    
    # Find courses similar to what the user is already taking
    recommended_courses = Course.objects.exclude(
        id__in=enrolled_course_ids
    ).annotate(
        students_count=Count('enrollments')
    ).order_by('-students_count')[:3]
    
    context = {
        'enrolled_courses': enrolled_courses,
        'completed_courses': completed_courses,
        'certificates': certificates,
        'certificates_count': certificates_count,
        'average_progress': round(average_progress, 1),
        'recent_notifications': recent_notifications,
        'recommended_courses': recommended_courses,
    }
    return render(request, 'student/dashboard.html', context)

def about(request):
    """About page view"""
    return render(request, 'core/about.html')

def contact(request):
    """Contact page view"""
    return render(request, 'core/contact.html')

def handler404(request, exception):
    """Custom 404 handler"""
    return render(request, 'errors/404.html', status=404)

def handler500(request):
    """Custom 500 handler"""
    return render(request, 'errors/500.html', status=500)

def handler403(request, exception):
    """Custom 403 handler"""
    return render(request, 'errors/403.html', status=403)

def handler400(request, exception):
    """Custom 400 handler"""
    return render(request, 'errors/400.html', status=400)