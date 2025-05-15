from rest_framework import serializers
from .models import Course
from lessons.models import Lesson
from accounts.serializers import UserSerializer

class CourseSerializer(serializers.ModelSerializer):
    instructor_name = serializers.SerializerMethodField()
    lessons_count = serializers.SerializerMethodField()
    enrollments_count = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ['id', 'title', 'description', 'instructor', 'instructor_name', 
                  'start_date', 'end_date', 'lessons_count', 'enrollments_count', 
                  'is_active', 'created_at', 'updated_at']
        read_only_fields = ['instructor', 'created_at', 'updated_at']

    def get_instructor_name(self, obj):
        return f"{obj.instructor.first_name} {obj.instructor.last_name}"

    def get_lessons_count(self, obj):
        return obj.get_lessons_count()

    def get_enrollments_count(self, obj):
        return obj.get_enrollments_count()

    def get_is_active(self, obj):
        return obj.is_active()

class LessonBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ['id', 'title', 'order']

class CourseDetailSerializer(CourseSerializer):
    instructor = UserSerializer(read_only=True)
    lessons = LessonBriefSerializer(many=True, read_only=True, source='lessons.all')

    class Meta(CourseSerializer.Meta):
        fields = CourseSerializer.Meta.fields + ['lessons']

class CourseStatisticsSerializer(serializers.ModelSerializer):
    total_students = serializers.SerializerMethodField()
    total_lessons = serializers.SerializerMethodField()
    lesson_completion_rate = serializers.SerializerMethodField()
    quiz_statistics = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = ['id', 'title', 'total_students', 'total_lessons', 
                  'lesson_completion_rate', 'quiz_statistics']
    
    def get_total_students(self, obj):
        return obj.enrollments.filter(status='enrolled').count()
    
    def get_total_lessons(self, obj):
        return obj.lessons.count()
    
    def get_lesson_completion_rate(self, obj):
        enrollments = obj.enrollments.filter(status='enrolled')
        if not enrollments:
            return 0
        
        total_progress_entries = 0
        completed_progress_entries = 0
        
        for enrollment in enrollments:
            lessons = obj.lessons.all()
            for lesson in lessons:
                progress_entries = lesson.progress_records.filter(user=enrollment.user)
                total_progress_entries += progress_entries.count()
                completed_progress_entries += progress_entries.filter(status='completed').count()
        
        if total_progress_entries == 0:
            return 0
        
        return round((completed_progress_entries / total_progress_entries) * 100, 2)
    
    def get_quiz_statistics(self, obj):
        quizzes = obj.quizzes.all()
        quiz_stats = []
        
        for quiz in quizzes:
            total_attempts = 0
            total_score = 0
            questions = quiz.questions.all()
            
            for question in questions:
                answers = question.answers.all()
                total_attempts += answers.count()
                for answer in answers:
                    total_score += answer.marks_obtained
            
            average_score = 0
            if total_attempts > 0:
                average_score = round(total_score / total_attempts, 2)
            
            quiz_stats.append({
                'quiz_id': quiz.id,
                'quiz_title': quiz.title,
                'total_attempts': total_attempts,
                'average_score': average_score
            })
        
        return quiz_stats