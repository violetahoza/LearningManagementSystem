from rest_framework import serializers
from .models import Progress
from lessons.models import Lesson
from accounts.serializers import UserSerializer
from lessons.serializers import LessonSerializer

class ProgressSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    lesson_details = LessonSerializer(source='lesson', read_only=True)
    
    class Meta:
        model = Progress
        fields = ['id', 'user', 'lesson', 'status', 'last_accessed', 
                  'user_details', 'lesson_details']
        read_only_fields = ['user', 'last_accessed']
    
    def create(self, validated_data):
        # Set the user to the current request user
        validated_data['user'] = self.context['request'].user
        
        # Check if progress already exists for this user and lesson
        lesson = validated_data.get('lesson')
        user = validated_data.get('user')
        
        progress, created = Progress.objects.get_or_create(
            lesson=lesson, 
            user=user,
            defaults={'status': validated_data.get('status', Progress.NOT_STARTED)}
        )
        
        if not created:
            # Update existing progress
            progress.status = validated_data.get('status', progress.status)
            progress.save()
        
        return progress

class CourseProgressSerializer(serializers.Serializer):
    course_id = serializers.IntegerField()
    course_title = serializers.CharField(read_only=True)
    total_lessons = serializers.IntegerField(read_only=True)
    completed_lessons = serializers.IntegerField(read_only=True)
    in_progress_lessons = serializers.IntegerField(read_only=True)
    not_started_lessons = serializers.IntegerField(read_only=True)
    completion_percentage = serializers.FloatField(read_only=True)
    
    def validate_course_id(self, value):
        from courses.models import Course
        from enrollments.models import Enrollment
        
        # Check if course exists
        try:
            course = Course.objects.get(pk=value)
        except Course.DoesNotExist:
            raise serializers.ValidationError("Course not found.")
        
        # Check if user is enrolled in the course
        user = self.context['request'].user
        if not Enrollment.objects.filter(user=user, course=course, status=Enrollment.ENROLLED).exists():
            raise serializers.ValidationError("You are not enrolled in this course.")
        
        return value
    
    def to_representation(self, instance):
        from courses.models import Course
        
        course_id = instance.get('course_id')
        user = self.context['request'].user
        
        course = Course.objects.get(pk=course_id)
        lessons = course.lessons.all()
        total_lessons = lessons.count()
        
        # Count progress for each lesson
        completed = 0
        in_progress = 0
        not_started = 0
        
        for lesson in lessons:
            progress = Progress.objects.filter(user=user, lesson=lesson).first()
            
            if not progress:
                not_started += 1
            elif progress.status == Progress.COMPLETED:
                completed += 1
            elif progress.status == Progress.IN_PROGRESS:
                in_progress += 1
            else:
                not_started += 1
        
        # Calculate completion percentage
        completion_percentage = 0
        if total_lessons > 0:
            completion_percentage = (completed / total_lessons) * 100
        
        # Check if course is completed and if so, issue certificate
        if completion_percentage == 100:
            try:
                from certificates.models import Certificate
                from enrollments.models import Enrollment
                
                # Update enrollment status
                enrollment = Enrollment.objects.get(user=user, course=course)
                enrollment.status = Enrollment.COMPLETED
                enrollment.save()
                
                # Issue certificate if not already issued
                if not Certificate.objects.filter(user=user, course=course).exists():
                    Certificate.objects.create(user=user, course=course)
                    
                    # Create notification for certificate issuance
                    from notifications.models import Notification
                    Notification.objects.create(
                        user=user,
                        title=f"Certificate Issued: {course.title}",
                        message=f"Congratulations! You have been issued a certificate for completing {course.title}.",
                        notification_type=Notification.CERTIFICATE_ISSUED
                    )
            except:
                # Fail silently if certificate creation fails
                pass
        
        return {
            'course_id': course_id,
            'course_title': course.title,
            'total_lessons': total_lessons,
            'completed_lessons': completed,
            'in_progress_lessons': in_progress,
            'not_started_lessons': not_started,
            'completion_percentage': round(completion_percentage, 2)
        }