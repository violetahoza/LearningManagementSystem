from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg
from courses.models import Course
from enrollments.models import Enrollment
from certificates.models import Certificate
from notifications.models import Notification
from progress.models import Progress

def home(request):
    """Home page view"""
    # Get featured courses (e.g., most popular courses)
    featured_courses = Course.objects.all().order_by('-id')[:4]
    
    context = {
        'featured_courses': featured_courses,
    }
    return render(request, 'core/home.html', context)

@login_required
def dashboard(request):
    """Dashboard view - redirects to appropriate dashboard based on user role"""
    user = request.user
    
    if user.is_admin():
        return redirect('admin:index')
    elif user.is_teacher():
        return redirect('courses:teacher_dashboard')
    else:  # student
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
        
        context = {
            'enrolled_courses': enrolled_courses,
            'completed_courses': completed_courses,
            'certificates': certificates,
            'certificates_count': certificates_count,
            'average_progress': round(average_progress, 1),
            'recent_notifications': recent_notifications,
        }
        return render(request, 'student/dashboard.html', context)

def about(request):
    """About page view"""
    return render(request, 'core/about.html')

def contact(request):
    """Contact page view"""
    return render(request, 'core/contact.html')