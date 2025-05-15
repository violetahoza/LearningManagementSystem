from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from courses.models import Course
from enrollments.models import Enrollment

def home(request):
    """Home page view"""
    # Get featured courses (e.g., most popular courses)
    featured_courses = Course.objects.all().order_by('-enrollments')[:4]
    
    context = {
        'featured_courses': featured_courses,
    }
    return render(request, 'core/home.html', context)

@login_required
def dashboard(request):
    """Dashboard view - redirects to appropriate dashboard based on user role"""
    user = request.user
    
    if user.is_admin():
        return redirect('admin:dashboard')
    elif user.is_teacher():
        return redirect('courses:teacher_dashboard')
    else:  # student
        # Get enrolled courses for student dashboard
        enrolled_courses = Enrollment.objects.filter(
            user=user, 
            status=Enrollment.ENROLLED
        ).select_related('course')
        
        context = {
            'enrolled_courses': enrolled_courses,
        }
        return render(request, 'student/dashboard.html', context)

def about(request):
    """About page view"""
    return render(request, 'core/about.html')

def contact(request):
    """Contact page view"""
    return render(request, 'core/contact.html')