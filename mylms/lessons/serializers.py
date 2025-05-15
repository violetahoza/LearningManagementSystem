from rest_framework import serializers
from .models import Lesson
from courses.models import Course

class LessonSerializer(serializers.ModelSerializer):
    course_title = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = ['id', 'course', 'course_title', 'title', 'content', 
                  'video_url', 'order', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
    
    def get_course_title(self, obj):
        return obj.course.title
    
    def validate_course(self, value):
        user = self.context['request'].user
        # Only instructors who own the course can create/update lessons
        if user.is_teacher() and value.instructor != user:
            raise serializers.ValidationError("You can only create lessons for courses you instruct.")
        return value

class LessonDetailSerializer(LessonSerializer):
    class Meta(LessonSerializer.Meta):
        pass
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        user = self.context['request'].user
        
        # If user is a student enrolled in this course, update their progress
        if user.is_student():
            from progress.models import Progress
            progress, created = Progress.objects.get_or_create(
                user=user,
                lesson=instance,
                defaults={'status': Progress.IN_PROGRESS if created else Progress.NOT_STARTED}
            )
            
            if created or progress.status == Progress.NOT_STARTED:
                progress.status = Progress.IN_PROGRESS
                progress.save()
            
            representation['progress_status'] = progress.status
            
        return representation