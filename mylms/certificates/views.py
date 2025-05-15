from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, HttpResponseForbidden
from django.template.loader import render_to_string
from django.utils import timezone
import uuid
from .models import Certificate
from courses.models import Course
from accounts.models import User
from enrollments.models import Enrollment
from progress.models import Progress
from lessons.models import Lesson
from notifications.models import Notification

@login_required
def certificate_list(request):
    """View list of certificates for the current user"""
    if request.user.is_student():
        # Students see their own certificates
        certificates = Certificate.objects.filter(user=request.user).select_related('course')
    elif request.user.is_teacher():
        # Teachers see certificates for their courses
        certificates = Certificate.objects.filter(course__instructor=request.user).select_related('course', 'user')
    elif request.user.is_admin():
        # Admins see all certificates
        certificates = Certificate.objects.all().select_related('course', 'user')
    else:
        return HttpResponseForbidden("Access denied")
    
    context = {
        'certificates': certificates,
        'is_student': request.user.is_student()
    }
    return render(request, 'certificates/certificate_list.html', context)

@login_required
def certificate_detail(request, certificate_id):
    """View certificate details"""
    certificate = get_object_or_404(Certificate, id=certificate_id)
    
    # Check permissions
    if request.user != certificate.user and \
       request.user != certificate.course.instructor and \
       not request.user.is_admin():
        return HttpResponseForbidden("Access denied")
    
    context = {
        'certificate': certificate
    }
    return render(request, 'certificates/certificate_detail.html', context)

@login_required
def download_certificate(request, certificate_id):
    """Download certificate as PDF"""
    certificate = get_object_or_404(Certificate, id=certificate_id)
    
    # Check permissions
    if request.user != certificate.user and \
       request.user != certificate.course.instructor and \
       not request.user.is_admin():
        return HttpResponseForbidden("Access denied")
    
    # In a real implementation, we would generate a PDF here
    # For this example, we'll just render a printable HTML version
    context = {
        'certificate': certificate,
        'print_view': True
    }
    return render(request, 'certificates/certificate_pdf.html', context)

@login_required
def generate_certificate(request, course_id, student_id):
    """Generate a certificate for a student"""
    if not request.user.is_teacher() and not request.user.is_admin():
        return HttpResponseForbidden("Only teachers and administrators can generate certificates")
    
    course = get_object_or_404(Course, id=course_id)
    student = get_object_or_404(User, id=student_id, role=User.STUDENT)
    
    # Check if the teacher is the course instructor
    if not request.user.is_admin() and course.instructor != request.user:
        return HttpResponseForbidden("You can only generate certificates for your courses")
    
    # Check if student is enrolled and has completed the course
    enrollment = get_object_or_404(Enrollment, user=student, course=course)
    
    # Check if certificate already exists
    if Certificate.objects.filter(user=student, course=course).exists():
        messages.warning(request, f"Certificate already exists for {student.get_full_name()} in this course")
        return redirect('progress:student_progress', student_id=student_id, course_id=course_id)
    
    # Check course completion if not admin
    if not request.user.is_admin():
        lessons = Lesson.objects.filter(course=course)
        completed_lessons = Progress.objects.filter(
            user=student,
            lesson__course=course,
            status=Progress.COMPLETED
        ).count()
        
        if completed_lessons < lessons.count():
            messages.error(request, f"{student.get_full_name()} has not completed all lessons in this course")
            return redirect('progress:student_progress', student_id=student_id, course_id=course_id)
    
    # Generate certificate code
    certificate_code = f"{student.id}-{course.id}-{uuid.uuid4().hex[:8].upper()}"
    
    # Create certificate
    certificate = Certificate.objects.create(
        user=student,
        course=course,
        certificate_code=certificate_code
    )
    
    # Update enrollment status
    enrollment.status = Enrollment.COMPLETED
    enrollment.save()
    
    # Create notification
    Notification.objects.create(
        user=student,
        title=f"Certificate Issued: {course.title}",
        message=f"Congratulations! You have been issued a certificate for completing {course.title}.",
        notification_type=Notification.CERTIFICATE_ISSUED
    )
    
    messages.success(request, f"Certificate generated for {student.get_full_name()}")
    return redirect('certificates:certificate_detail', certificate_id=certificate.id)

def verify_certificate(request, certificate_code):
    """Verify a certificate by its code"""
    certificate = get_object_or_404(Certificate, certificate_code=certificate_code)
    
    context = {
        'certificate': certificate,
        'is_verified': True
    }
    return render(request, 'certificates/certificate_verify.html', context)