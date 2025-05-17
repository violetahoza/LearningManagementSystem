from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.utils import timezone
from django.db.models import Count, Sum
import logging

from accounts.models import User
from .forms import UserCreationAdminForm, UserEditAdminForm
from courses.models import Course
from enrollments.models import Enrollment
from certificates.models import Certificate
from notifications.models import Notification

# Get logger
logger = logging.getLogger('user_activity')

# Helper function to check if user is admin
def is_admin(user):
    return user.is_authenticated and user.is_admin()

@login_required
@user_passes_test(is_admin)
def user_list(request):
    """View to list all users with filtering options"""
    # Get filter parameters
    role_filter = request.GET.get('role', '')
    search_query = request.GET.get('q', '')
    
    # Base queryset
    users = User.objects.all()
    
    # Apply filters
    if role_filter:
        users = users.filter(role=role_filter)
    
    if search_query:
        users = users.filter(
            username__icontains=search_query
        ) | users.filter(
            email__icontains=search_query
        ) | users.filter(
            first_name__icontains=search_query
        ) | users.filter(
            last_name__icontains=search_query
        )
    
    # Get statistics
    total_users = User.objects.count()
    total_students = User.objects.filter(role=User.STUDENT).count()
    total_teachers = User.objects.filter(role=User.TEACHER).count()
    total_admins = User.objects.filter(role=User.ADMIN).count()
    
    # Recently registered users (last 30 days)
    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
    recent_users = User.objects.filter(date_joined__gte=thirty_days_ago).count()
    
    context = {
        'users': users,
        'total_users': total_users,
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_admins': total_admins,
        'recent_users': recent_users,
        'role_filter': role_filter,
        'search_query': search_query,
    }
    
    return render(request, 'admin/user_list.html', context)

@login_required
@user_passes_test(is_admin)
def create_user(request):
    """View to create a new user"""
    if request.method == 'POST':
        form = UserCreationAdminForm(request.POST)
        if form.is_valid():
            user = form.save()
            logger.info(f"Admin {request.user.username} (ID: {request.user.id}) created user {user.username} (ID: {user.id})")
            messages.success(request, f"User '{user.username}' has been created successfully.")
            return redirect('admin:user_list')
    else:
        form = UserCreationAdminForm()
    
    context = {
        'form': form,
        'action': 'Create'
    }
    return render(request, 'admin/user_form.html', context)

@login_required
@user_passes_test(is_admin)
def edit_user(request, user_id):
    """View to edit an existing user"""
    user_to_edit = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = UserEditAdminForm(request.POST, instance=user_to_edit)
        if form.is_valid():
            form.save()
            logger.info(f"Admin {request.user.username} (ID: {request.user.id}) updated user {user_to_edit.username} (ID: {user_to_edit.id})")
            messages.success(request, f"User '{user_to_edit.username}' has been updated successfully.")
            return redirect('admin:user_list')
    else:
        form = UserEditAdminForm(instance=user_to_edit)
    
    context = {
        'form': form,
        'user_to_edit': user_to_edit,
        'action': 'Edit'
    }
    return render(request, 'admin/user_form.html', context)

@login_required
@user_passes_test(is_admin)
def delete_user(request, user_id):
    """View to delete a user"""
    user_to_delete = get_object_or_404(User, id=user_id)
    
    if request.user.id == user_to_delete.id:
        messages.error(request, "You cannot delete your own account.")
        return redirect('admin:user_list')
    
    if request.method == 'POST':
        username = user_to_delete.username
        logger.info(f"Admin {request.user.username} (ID: {request.user.id}) deleted user {username} (ID: {user_to_delete.id})")
        user_to_delete.delete()
        messages.success(request, f"User '{username}' has been deleted.")
        return redirect('admin:user_list')
    
    context = {
        'user_to_delete': user_to_delete,
    }
    return render(request, 'admin/user_confirm_delete.html', context)

@login_required
@user_passes_test(is_admin)
def user_detail(request, user_id):
    """View to see detailed information about a user"""
    user_to_view = get_object_or_404(User, id=user_id)
    
    if user_to_view.is_student():
        # Get student-specific data
        enrollments = Enrollment.objects.filter(user=user_to_view)
        certificates = Certificate.objects.filter(user=user_to_view)
        
        # Calculate progress statistics
        enrollment_stats = {
            'total': enrollments.count(),
            'active': enrollments.filter(status=Enrollment.ENROLLED).count(),
            'completed': enrollments.filter(status=Enrollment.COMPLETED).count(),
            'dropped': enrollments.filter(status=Enrollment.DROPPED).count(),
        }
        
        context = {
            'user_to_view': user_to_view,
            'enrollments': enrollments,
            'certificates': certificates,
            'enrollment_stats': enrollment_stats,
            'user_type': 'student'
        }
    
    elif user_to_view.is_teacher():
        # Get teacher-specific data
        courses = Course.objects.filter(instructor=user_to_view)
        
        # Calculate teaching statistics
        student_count = Enrollment.objects.filter(
            course__instructor=user_to_view
        ).values('user').distinct().count()
        
        active_courses_count = Course.objects.filter(
            instructor=user_to_view,
            start_date__lte=timezone.now().date(),
            end_date__gte=timezone.now().date()
        ).count()
        
        completion_rate = 0
        enrollments = Enrollment.objects.filter(course__instructor=user_to_view)
        if enrollments.exists():
            completed = enrollments.filter(status=Enrollment.COMPLETED).count()
            completion_rate = (completed / enrollments.count()) * 100
        
        context = {
            'user_to_view': user_to_view,
            'courses': courses,
            'student_count': student_count,
            'active_courses_count': active_courses_count,
            'completion_rate': round(completion_rate, 1),
            'user_type': 'teacher'
        }
    
    else:  # Admin user
        context = {
            'user_to_view': user_to_view,
            'user_type': 'admin'
        }
    
    return render(request, 'admin/user_detail.html', context)

@login_required
@user_passes_test(is_admin)
def system_stats(request):
    """View to display detailed system statistics"""
    # Users statistics
    user_stats = {
        'total': User.objects.count(),
        'students': User.objects.filter(role=User.STUDENT).count(),
        'teachers': User.objects.filter(role=User.TEACHER).count(),
        'admins': User.objects.filter(role=User.ADMIN).count(),
    }
    
    # Course statistics
    course_stats = {
        'total': Course.objects.count(),
        'active': Course.objects.filter(
            start_date__lte=timezone.now().date(),
            end_date__gte=timezone.now().date()
        ).count(),
        'upcoming': Course.objects.filter(
            start_date__gt=timezone.now().date()
        ).count(),
        'completed': Course.objects.filter(
            end_date__lt=timezone.now().date()
        ).count(),
    }
    
    # Enrollment statistics
    enrollment_stats = {
        'total': Enrollment.objects.count(),
        'active': Enrollment.objects.filter(status=Enrollment.ENROLLED).count(),
        'completed': Enrollment.objects.filter(status=Enrollment.COMPLETED).count(),
        'dropped': Enrollment.objects.filter(status=Enrollment.DROPPED).count(),
    }
    
    # Certificate statistics
    certificate_stats = {
        'total': Certificate.objects.count(),
        'last_30_days': Certificate.objects.filter(
            issue_date__gte=timezone.now() - timezone.timedelta(days=30)
        ).count(),
    }
    
    # Timeline data (monthly registrations)
    six_months_ago = timezone.now() - timezone.timedelta(days=180)
    monthly_registrations = []
    
    for i in range(6):
        month_start = six_months_ago + timezone.timedelta(days=30 * i)
        month_end = six_months_ago + timezone.timedelta(days=30 * (i + 1))
        
        count = User.objects.filter(
            date_joined__gte=month_start,
            date_joined__lt=month_end
        ).count()
        
        monthly_registrations.append({
            'month': month_start.strftime('%b %Y'),
            'count': count
        })
    
    # Popular courses (by enrollment count)
    popular_courses = Course.objects.annotate(
        enrollment_count=Count('enrollments')
    ).order_by('-enrollment_count')[:5]
    
    # Active teachers (by course count)
    active_teachers = User.objects.filter(
        role=User.TEACHER
    ).annotate(
        course_count=Count('courses')
    ).filter(
        course_count__gt=0
    ).order_by('-course_count')[:5]
    
    context = {
        'user_stats': user_stats,
        'course_stats': course_stats,
        'enrollment_stats': enrollment_stats,
        'certificate_stats': certificate_stats,
        'monthly_registrations': monthly_registrations,
        'popular_courses': popular_courses,
        'active_teachers': active_teachers,
    }
    
    return render(request, 'admin/system_stats.html', context)

@login_required
@user_passes_test(is_admin)
def send_notification(request):
    """View to send notification to users"""
    if request.method == 'POST':
        notification_type = request.POST.get('notification_type')
        title = request.POST.get('title')
        message = request.POST.get('message')
        recipient_type = request.POST.get('recipient_type')
        
        # Validate inputs
        if not title or not message:
            messages.error(request, "Title and message are required.")
            return redirect('admin:send_notification')
        
        # Determine recipients based on type
        if recipient_type == 'all':
            recipients = User.objects.all()
        elif recipient_type == 'students':
            recipients = User.objects.filter(role=User.STUDENT)
        elif recipient_type == 'teachers':
            recipients = User.objects.filter(role=User.TEACHER)
        elif recipient_type == 'course':
            course_id = request.POST.get('course_id')
            if not course_id:
                messages.error(request, "Course ID is required for course-specific notifications.")
                return redirect('admin:send_notification')
            
            # Get all students enrolled in the course
            recipients = User.objects.filter(
                enrollments__course_id=course_id,
                enrollments__status=Enrollment.ENROLLED
            )
        else:
            messages.error(request, "Invalid recipient type.")
            return redirect('admin:send_notification')
        
        # Create notifications for each recipient
        notification_count = 0
        for user in recipients:
            Notification.objects.create(
                user=user,
                title=title,
                message=message,
                notification_type=notification_type or Notification.GENERAL
            )
            notification_count += 1
        
        logger.info(f"Admin {request.user.username} (ID: {request.user.id}) sent notification '{title}' to {notification_count} users")
        messages.success(request, f"Notification sent to {notification_count} users.")
        return redirect('admin:dashboard')
    
    # Get courses for the dropdown
    courses = Course.objects.all()
    
    context = {
        'courses': courses,
        'notification_types': Notification.NOTIFICATION_TYPE_CHOICES
    }
    
    return render(request, 'admin/send_notification.html', context)

@login_required
@user_passes_test(is_admin)
def course_management(request):
    """View to manage all courses"""
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('q', '')
    
    # Base queryset
    courses = Course.objects.all()
    
    # Apply filters
    if status_filter == 'active':
        courses = courses.filter(
            start_date__lte=timezone.now().date(),
            end_date__gte=timezone.now().date()
        )
    elif status_filter == 'upcoming':
        courses = courses.filter(start_date__gt=timezone.now().date())
    elif status_filter == 'completed':
        courses = courses.filter(end_date__lt=timezone.now().date())
    
    if search_query:
        courses = courses.filter(
            title__icontains=search_query
        ) | courses.filter(
            description__icontains=search_query
        ) | courses.filter(
            instructor__username__icontains=search_query
        )
    
    # Annotate with enrollment counts
    courses = courses.annotate(
        enrollment_count=Count('enrollments'),
        completed_count=Count('enrollments', filter={'enrollments__status': Enrollment.COMPLETED})
    )
    
    # Course statistics
    course_stats = {
        'total': Course.objects.count(),
        'active': Course.objects.filter(
            start_date__lte=timezone.now().date(),
            end_date__gte=timezone.now().date()
        ).count(),
        'upcoming': Course.objects.filter(
            start_date__gt=timezone.now().date()
        ).count(),
        'completed': Course.objects.filter(
            end_date__lt=timezone.now().date()
        ).count(),
    }
    
    # Total enrollment statistics
    total_enrollments = Enrollment.objects.count()
    
    context = {
        'courses': courses,
        'course_stats': course_stats,
        'total_enrollments': total_enrollments,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    
    return render(request, 'admin/course_management.html', context)