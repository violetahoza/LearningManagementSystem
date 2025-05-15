from rest_framework import serializers
from .models import Certificate
from accounts.serializers import UserSerializer
from courses.serializers import CourseSerializer

class CertificateSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    course_details = CourseSerializer(source='course', read_only=True)
    
    class Meta:
        model = Certificate
        fields = ['id', 'user', 'course', 'certificate_code', 'issue_date', 
                  'user_details', 'course_details']
        read_only_fields = ['user', 'certificate_code', 'issue_date']
