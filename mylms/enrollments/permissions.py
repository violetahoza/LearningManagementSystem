from rest_framework import permissions

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to view or edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Admins can do anything
        if request.user.is_admin():
            return True
        
        # Teachers can see enrollments for their courses
        if request.user.is_teacher() and obj.course.instructor == request.user:
            return True
        
        # Students can only see their own enrollments
        return obj.user == request.user