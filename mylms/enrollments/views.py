from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Enrollment
from courses.models import Course
from .serializers import EnrollmentSerializer
from .permissions import IsOwnerOrAdmin

class EnrollmentViewSet(viewsets.ModelViewSet):
    queryset = Enrollment.objects.all()
    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    
    def get_queryset(self):
        # Admins can see all enrollments
        if self.request.user.is_admin():
            return Enrollment.objects.all()
        
        # Teachers can see enrollments for their courses
        if self.request.user.is_teacher():
            return Enrollment.objects.filter(course__instructor=self.request.user)
        
        # Students can see only their enrollments
        return Enrollment.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def enroll(self, request):
        """Enroll the current user in a course"""
        course_id = request.data.get('course_id')
        if not course_id:
            return Response({"detail": "Course ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        course = get_object_or_404(Course, id=course_id)
        
        # Check if already enrolled
        if Enrollment.objects.filter(user=request.user, course=course).exists():
            return Response({"detail": "You are already enrolled in this course."},
                           status=status.HTTP_400_BAD_REQUEST)
        
        enrollment = Enrollment.objects.create(
            user=request.user,
            course=course,
            status=Enrollment.ENROLLED
        )
        
        return Response(EnrollmentSerializer(enrollment).data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update the status of an enrollment"""
        enrollment = self.get_object()
        status_value = request.data.get('status')
        
        if not status_value or status_value not in [s[0] for s in Enrollment.STATUS_CHOICES]:
            return Response({"detail": "Valid status is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        enrollment.status = status_value
        enrollment.save()
        
        return Response(EnrollmentSerializer(enrollment).data)