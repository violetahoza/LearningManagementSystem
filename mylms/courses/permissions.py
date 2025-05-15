from rest_framework import permissions

class IsInstructorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow instructors to create or edit courses.
    """
    
    def has_permission(self, request, view):
        # Allow read access for anyone
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for teachers
        return request.user.is_authenticated and request.user.is_teacher()
    
    def has_object_permission(self, request, view, obj):
        # Allow read access for anyone
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Only allow editing by the instructor who created the course or by admins
        return request.user.is_authenticated and (
            obj.instructor == request.user or request.user.is_admin()
        )

class IsEnrolledOrInstructor(permissions.BasePermission):
    """
    Custom permission to only allow access to course content for enrolled students or the instructor.
    """
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        if not user.is_authenticated:
            return False
        
        # Admins can access everything
        if user.is_admin():
            return True
        
        # Instructors can access their own courses
        if user.is_teacher() and obj.instructor == user:
            return True
        
        # Students can access courses they're enrolled in
        if user.is_student():
            from enrollments.models import Enrollment
            return Enrollment.objects.filter(
                user=user, 
                course=obj, 
                status=Enrollment.ENROLLED
            ).exists()
        
        return False