from rest_framework import serializers
from .models import Enrollment
from courses.models import Course
from accounts.serializers import UserSerializer
from courses.serializers import CourseSerializer

class EnrollmentSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    course_details = CourseSerializer(source='course', read_only=True)
    
    class Meta:
        model = Enrollment
        fields = ['id', 'user', 'course', 'status', 'enrolled_at', 
                  'updated_at', 'user_details', 'course_details']
        read_only_fields = ['user', 'enrolled_at', 'updated_at']
        
    def validate(self, attrs):
        # Make sure user isn't already enrolled in this course
        user = self.context['request'].user
        course = attrs.get('course')
        
        if course and Enrollment.objects.filter(user=user, course=course).exists():
            raise serializers.ValidationError("You are already enrolled in this course.")
        
        return attrs