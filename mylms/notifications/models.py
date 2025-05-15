from django.db import models
from accounts.models import User

class Notification(models.Model):
    LESSON_ADDED = 'lesson_added'
    ENROLLMENT = 'enrollment'
    COURSE_COMPLETED = 'course_completed'
    QUIZ_GRADED = 'quiz_graded'
    CERTIFICATE_ISSUED = 'certificate_issued'
    GENERAL = 'general'
    
    NOTIFICATION_TYPE_CHOICES = [
        (LESSON_ADDED, 'Lesson Added'),
        (ENROLLMENT, 'Enrollment'),
        (COURSE_COMPLETED, 'Course Completed'),
        (QUIZ_GRADED, 'Quiz Graded'),
        (CERTIFICATE_ISSUED, 'Certificate Issued'),
        (GENERAL, 'General'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"