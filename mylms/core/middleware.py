from django.conf import settings
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
import re

class SecurityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # Paths that should be accessible only to authenticated users
        self.secure_paths = [
            r'^/courses/(?!$)', 
            r'^/lessons/',
            r'^/quizzes/',
            r'^/progress/',
            r'^/certificates/',
            r'^/notifications/',
            r'^/accounts/profile/'
        ]
        # Exceptions - paths that match secure paths but should be public
        self.public_exceptions = [
            r'^/courses/$',
            r'^/courses/\d+/$'
        ]
        # Role-based access control
        self.admin_only_paths = [
            r'^/admin/',
        ]
        self.teacher_only_paths = [
            r'^/courses/create/',
            r'^/courses/\d+/edit/',
            r'^/courses/\d+/delete/',
            r'^/courses/\d+/students/',
            r'^/courses/dashboard/',
            r'^/lessons/course/\d+/create/',
            r'^/lessons/\d+/edit/',
            r'^/lessons/\d+/delete/',
            r'^/quizzes/course/\d+/create/',
            r'^/quizzes/\d+/edit/',
            r'^/quizzes/\d+/delete/',
            r'^/quizzes/\d+/questions/',
            r'^/quizzes/\d+/statistics/',
            r'^/certificates/generate/'
        ]
        self.student_only_paths = [
            r'^/courses/\d+/enroll/',
            r'^/quizzes/\d+/attempt/',
            r'^/quizzes/\d+/submit/',
            r'^/lessons/\d+/mark-complete/'
        ]

    def __call__(self, request):
        path = request.path
        user = request.user

        # Check for secure paths that require authentication
        requires_auth = any(re.match(pattern, path) for pattern in self.secure_paths)
        public_exception = any(re.match(pattern, path) for pattern in self.public_exceptions)

        if requires_auth and not public_exception and not user.is_authenticated:
            messages.warning(request, "You need to be logged in to access this page.")
            return redirect(f"{reverse('accounts:login')}?next={path}")

        # Role-based access control
        if user.is_authenticated:
            # Admin only paths
            if any(re.match(pattern, path) for pattern in self.admin_only_paths) and not user.is_admin():
                messages.error(request, "Access denied. Admin privileges required.")
                return redirect('core:dashboard')

            # Teacher only paths
            if any(re.match(pattern, path) for pattern in self.teacher_only_paths) and not user.is_teacher() and not user.is_admin():
                messages.error(request, "Access denied. Teacher privileges required.")
                return redirect('core:dashboard')

            # Student only paths
            if any(re.match(pattern, path) for pattern in self.student_only_paths) and not user.is_student():
                messages.error(request, "Access denied. Student privileges required.")
                return redirect('core:dashboard')

        # Security headers
        response = self.get_response(request)
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        
        if settings.DEBUG is False:
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            
        return response